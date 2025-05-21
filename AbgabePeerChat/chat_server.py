import struct
import threading
from socket import socket

class Client:
    def __init__(self, _id, socket, address):
        self._id = _id
        self.socket = socket
        self.addr = address
        self.nickname = ""
        self.ip = ""
        self.udp_port = -1

class Server:
    def __init__(self):
        self.clients = []
        self.id = 0
        self.ip = '127.0.0.1'
        self.port = 22222
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen()

    def register_client(self, ip, nickname, udp_port):
        self.clients.append((ip, nickname, udp_port))

    def send_update(self):
        pass

    def send_bad_format(self, client_socket):
        pass

    def send_broadcast(self, client, nickname, message):
        combined_str = nickname + "|" + message
        body = combined_str.encode('utf-8')
        mes_len = len(body).to_bytes(4, byteorder='big')
        mes_id = (2).to_bytes(1, byteorder='big')
        outgoing_bytes = mes_len + mes_id + body
        client.socket.sendall(outgoing_bytes)


    def handle_client(self, client_socket, addr):
        while True:
            try:
                message_length = int.from_bytes(client_socket.recv(4), byteorder='big', signed=False)
                message_id = int.from_bytes(client_socket.recv(1), byteorder='big', signed=False)
                message = client_socket.recv(message_length).decode()
                if not message:
                    break
                local_client = None
                for x in self.clients:
                    if x.socket == client_socket:
                        local_client = x
                        break
                if message_id == 0:
                    #Anmeldung
                    splits = message.split("|")
                    local_client.nickname = splits[0]
                    local_client.ip = splits[1]
                    local_client.udp_port = splits[2]
                elif message_id == 1:
                    #Abmeldung
                    self.clients.remove(local_client)
                elif message_id == 2:
                    #Broadcast
                    for x in self.clients:
                        if x != local_client:
                            self.send_broadcast(x, local_client.nickname, message)


                print(f"Received from {addr}: {message}")
                client_socket.sendall(f"Echo: {message}".encode())
            except Exception as e:
                print(e)
                #send back 'bad format' message
                self.send_bad_format(client_socket)
                break
        client_socket.close()

    """
    0	Anmeldung
	1	Abmeldung
	(uint32_t)(uint8)nickname|ip-Adresse|UDP-Port
	2	Broadcast
	(uint32_t)(uint8)"Nachricht an alle"
    """


    def start_server(self):
        while True:
            client_socket, addr, = self.server_socket.accept()
            self.clients.append(Client(self.id, client_socket, addr))
            self.id += 1
            thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
            thread.start()
