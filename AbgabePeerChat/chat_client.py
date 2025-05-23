import threading
import time
from socket import socket
import socket

HOST = '127.0.0.1'
PORT = 22222

class Peer:
    def __init__(self, nickname, ip, udp_port: int):
        self.nickname = nickname
        self.ip = ip
        self.udp_port: int = udp_port

    def __eq__(self, other):
        return self.ip == other.ip and self.udp_port == other.udp_port and self.nickname == other.nickname

    def __str__(self):
        return self.nickname + ":" + self.ip + ":" + str(self.udp_port)

class Client:
    def __init__(self, nickname, ip, udp_port, tcp_port):
        self.nickname = nickname
        self.ip = ip
        self.udp_port = udp_port
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peer_list = []
        self.open_chat_sockets = []
        self.open_chat_sockets_lock = threading.Lock()
        self.tcp_port = tcp_port


    def send_registration(self):
        self.server_client_socket.connect((HOST, PORT))
        combined_str = self.nickname + "|" + self.ip + "|" + str(self.udp_port)
        body = combined_str.encode('utf-8')
        mes_len = len(body).to_bytes(4, byteorder='big')
        mes_id = (0).to_bytes(1, byteorder='big')
        outgoing_bytes = mes_len + mes_id + body
        self.server_client_socket.sendall(outgoing_bytes)

    def new_peer_update(self, message):
        splits = message.split("|")
        if len(splits) != 3:
            print("New peer update with length != 3")
            exit(1)
        self.peer_list.append(Peer(splits[0], splits[1], splits[2]))

    def del_peer_update(self, message):
        splits = message.split("|")
        if len(splits) != 3:
            print("Peer delete update with length != 3")
            exit(1)
        self.peer_list.remove(Peer(splits[0], splits[1], splits[2])) #overrode eq to value based eq

    def receive_broadcast(self, message):
        splits = message.split("|")
        if len(splits) != 2:
            print("Broadcast with length != 2")
            exit(1)
        print(f"Broadcast: \n{splits[0]} writes:\n\"{splits[1]}\"")

    def initialize_peer_list(self, message):
        if message:
            if "\n" in message:
                lines = message.split("\n")
                for line in lines:
                    splits = line.split("|")
                    self.peer_list.append(Peer(splits[0], splits[1], splits[2]))
            else:
                splits = message.split("|")
                self.peer_list.append(Peer(splits[0], splits[1], splits[2]))
        else:
            print("No peers online yet.")

    def send_broadcast(self, message):
        body = message.encode('utf-8')
        mes_len = len(body).to_bytes(4, byteorder='big')
        mes_id = (2).to_bytes(1, byteorder='big')
        outgoing_bytes = mes_len + mes_id + body
        self.server_client_socket.sendall(outgoing_bytes)

    def handle_bad_format_response(self):
        print("Received bad format response.")
        self.server_client_socket.close()
        exit(1)

    def handle_refused_registration(self):
        print("The server complained about your nickname. Please choose another nickname in this format: \"example\" <-- with the quotes!")
        old_name = self.nickname
        while old_name == self.nickname:
            time.sleep(1)
        self.send_registration()

    def log_out(self):
        combined_str = self.nickname + "|" + self.ip + "|" + str(self.udp_port)
        body = combined_str.encode('utf-8')
        mes_len = len(body).to_bytes(4, byteorder='big')
        mes_id = (1).to_bytes(1, byteorder='big')
        outgoing_bytes = mes_len + mes_id + body
        self.server_client_socket.sendall(outgoing_bytes)

    def handle_server_messages(self):
        while True:
            try:
                message_length = int.from_bytes(self.server_client_socket.recv(4), byteorder='big', signed=False)
                message_id = int.from_bytes(self.server_client_socket.recv(1), byteorder='big', signed=False)
                if message_length > 0:
                    message = self.server_client_socket.recv(message_length).decode("utf-8")
                else:
                    message = ""

                if message_id == 0:
                    self.new_peer_update(message)

                elif message_id == 1:
                    self.del_peer_update(message)

                elif message_id == 2:
                    self.receive_broadcast(message)

                elif message_id == 3:
                    self.initialize_peer_list(message)

                # message_id 4 is for peer2peer messages.

                elif message_id == 5:
                    self.handle_refused_registration()

                elif message_id == 6:
                    self.handle_bad_format_response()

                else:
                    print("Unknown message received.")
                    break


            except Exception as e:
                #print(e)
                break
        #self.log_out() # being friendly
        #self.client_socket.close()

    def change_username(self, username):
        self.nickname = username
        while True:
            if 20 >= len(self.nickname) >= 1 and "|" not in self.nickname:
                break
            self.nickname = input("Please choose another nickname in this format: \"example\" <-- with the quotes!")

    def initiate_peer_chat(self, peer_to_chat_with):
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_socket.bind((self.ip, self.tcp_port))
        peer_socket.listen()
        peer_socket.settimeout(3)
        peer_ip = ""
        peer_udp_port = -1
        for peer in self.peer_list:
            if peer_to_chat_with == peer.nickname:
                peer_ip = peer.ip
                peer_udp_port = peer.udp_port
        request_str = self.nickname + "|" + self.ip + "|" + str(self.tcp_port)
        request_body = request_str.encode('utf-8')
        request_len = len(request_body).to_bytes(4, byteorder='big')
        request_id = (4).to_bytes(1, byteorder='big')
        request = request_len + request_id + request_body
        self.udp_socket.sendto(request, (peer_ip, int(peer_udp_port)))
        peer_conn = None
        addr = -1
        try:
            peer_conn, addr = peer_socket.accept()
        except TimeoutError:
            pass
        if not peer_conn:
            self.udp_socket.sendto(request, (peer_ip, int(peer_udp_port)))
            try:
                peer_conn, addr = peer_socket.accept()
            except TimeoutError:
                print("Could not reach your peer.")
                return
        print("1")
        with self.open_chat_sockets_lock:
            self.open_chat_sockets.append((peer_conn, peer_to_chat_with))
        print("1,5")
        chat_thread = threading.Thread(target=self.chat_with_peer, args=(peer_to_chat_with,))
        chat_thread.start()
        print("2")

    def chat_with_peer(self, nickname):
        tcp_socket = None
        for sock in self.open_chat_sockets:
            if sock[1] == nickname:
                tcp_socket = sock[0]
        while True:
            try:
                message_length = int.from_bytes(tcp_socket.recv(4), byteorder='big', signed=False)
                message_id = int.from_bytes(tcp_socket.recv(1), byteorder='big', signed=False)
                if message_length > 0:
                    message = tcp_socket.recv(message_length).decode("utf-8")
                else:
                    message = ""

                if message_id == 4:
                    print(f"{nickname} an dich: {message}")
            except:
                pass
            time.sleep(1)

    def menu_options(self):
        print("Client menu options:\n    'p' see peer list\n    'b' send broadcast\n    'n' new peer chat\n    'm' message peer in open peer chat\n    'd' disconnect and quit")
        while True:
            user_input = input()
            if user_input.startswith("\""):
                self.change_username(user_input)

            elif user_input == "p":
                print(f"Peer list: \n{"\n".join([str(x) for x in self.peer_list])}")

            elif user_input == "b":
                message_input = input("Please enter the message to broadcast: ")
                self.send_broadcast(message_input)

            elif user_input == "d":
                print("Goodbye!")
                self.log_out()
                self.server_client_socket.close()
                break

            elif user_input == "n":
                print("Please type in the name of the peer you want to contact. ")
                print(f"Peer list: \n{"\n".join([str(x) for x in self.peer_list])}")
                peer_to_chat_with = input("start chat with: ")
                if peer_to_chat_with in [x.nickname for x in self.peer_list]:
                    self.initiate_peer_chat(peer_to_chat_with)
                else:
                    print(f"Could not find {peer_to_chat_with} in your peer list.")

            elif user_input == "m":
                peer_to_message = input("Plese enter the addressee's nickname: ")
                if peer_to_message in [x[1] for x in self.open_chat_sockets]:
                    message_to_peer = input(f"Plese enter the message to {peer_to_message}: ")
                    peers_socket = [x for x in self.open_chat_sockets if x[1] == peer_to_message][0][0]
                    body = message_to_peer.encode('utf-8')
                    mes_len = len(body).to_bytes(4, byteorder='big')
                    mes_id = (4).to_bytes(1, byteorder='big')
                    peers_socket.blocking(True)
                    peers_socket.sendall(mes_len + mes_id + body)
                    print("your message has been sent.")
                else:
                    print(f"Could not find peer called {peer_to_message} in your open chats.\nPlease type 'm', to try again, or 'n' to initiate a new chat.")

            time.sleep(1)

    def accept_peer_chat(self, nickname, ip, tcp_port):
        print(f"trying to accept peer chat with {nickname}, {ip}, {tcp_port}")
        tcp_chat_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_chat_socket.connect((ip, tcp_port))
        with self.open_chat_sockets_lock:
            self.open_chat_sockets.append((tcp_chat_socket, nickname))
        self.chat_with_peer(nickname)


    def handle_udp_chat_requests(self):
        self.udp_socket.bind((self.ip, self.udp_port))
        while True:
            try:
                mes_len, addr = self.udp_socket.recvfrom(4)
                mes_len = int.from_bytes(mes_len, byteorder='big', signed=False)
                mes_id = int.from_bytes(self.udp_socket.recv(1), byteorder='big', signed=False)
                message = self.udp_socket.recv(mes_len)
                message = message.decode('utf-8')
                splits = message.split("|")
                if len(splits) == 3:
                    peer_chat_thread = threading.Thread(target=self.accept_peer_chat, args=(splits[0], splits[1], int(splits[2])))
                    peer_chat_thread.start()

            except:
                pass


    def start_client(self):
        self.send_registration()
        server_thread = threading.Thread(target=self.handle_server_messages, args=())
        server_thread.start()
        menu_thread = threading.Thread(target=self.menu_options, args=())
        menu_thread.start()
        udp_thread = threading.Thread(target=self.handle_udp_chat_requests, args=())
        udp_thread.start()

        udp_thread.join()
        server_thread.join()
        menu_thread.join()

def main():
    while True:
        username = input("Please enter your nickname: ")
        if 20 >= len(username) >= 1 and "|" not in username:
            break
        else:
            print("Invalid nickname.")
    my_ip = "127.0.0.1"
    my_udp_port = 33333
    my_tcp_port = 23232
    you = Client(username, my_ip, my_udp_port, my_tcp_port)
    you.start_client()

main()


