import threading
import time
from socket import socket
import socket

HOST = '127.0.0.1'
PORT = 22222

class Peer:
    def __init__(self, nickname, ip, udp_port):
        self.nickname = nickname
        self.ip = ip
        self.udp_port = udp_port

    def __eq__(self, other):
        return self.ip == other.ip and self.udp_port == other.udp_port and self.nickname == other.nickname

class Client:
    def __init__(self, nickname, ip, udp_port):
        self.nickname = nickname
        self.ip = ip
        self.udp_port = udp_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peer_list = []
        self.reserve_user_input = threading.Lock()


    def send_registration(self):
        self.client_socket.connect((HOST, PORT))
        combined_str = self.nickname + "|" + self.ip + "|" + str(self.udp_port)
        body = combined_str.encode('utf-8')
        mes_len = len(body).to_bytes(4, byteorder='big')
        mes_id = (0).to_bytes(1, byteorder='big')
        outgoing_bytes = mes_len + mes_id + body
        self.client_socket.sendall(outgoing_bytes)

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
        pass

    def handle_bad_format_response(self):
        pass

    def handle_refused_registration(self):
        print("The server complained about your nickname. Please choose another nickname in this format: \"example\" <-- with the quotes!")
        old_name = self.nickname
        while old_name == self.nickname:
            time.sleep(1)
        self.send_registration()

    def handle_server_messages(self):
        while True:
            try:
                message_length = int.from_bytes(self.client_socket.recv(4), byteorder='big', signed=False)
                message_id = int.from_bytes(self.client_socket.recv(1), byteorder='big', signed=False)
                if message_length > 0:
                    message = self.client_socket.recv(message_length).decode()
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
                print(e)
                break
        self.client_socket.close()

    def change_username(self):
        while True:
            with self.reserve_user_input:
                self.nickname = input("new nickname: ")
            if 20 >= len(self.nickname) >= 1:
                break

    def menu_options(self):
        print("Client menu options:\n    'p' see peer list\n    'b' send broadcast\n    'n' new peer chat\n    'd' disconnect and quit")
        while True:
            with self.reserve_user_input:
                user_input = input()
            if user_input.startswith("\""):
                self.change_username()

            elif user_input == "p":
                print(f"Peer list: \n{self.peer_list}")

            time.sleep(1)

    def start_client(self):
        self.send_registration()
        server_thread = threading.Thread(target=self.handle_server_messages(), args=())
        server_thread.start()
        menu_thread = threading.Thread(target=self.menu_options, args=())
        menu_thread.start()

        server_thread.join()
        menu_thread.join()





        """
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((HOST, PORT))
            print("Connected to server.")
            while True:
                message = input("You: ")
                if message.lower() == 'exit':
                    break
                client_socket.sendall(message.encode())
                response = client_socket.recv(1024).decode()
                print(f"Server: {response}")
        """

