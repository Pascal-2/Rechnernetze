import threading
import socket

class Client_data:
    def __init__(self, _id, socket, address):
        self._id = _id
        self.socket = socket
        self.addr = address
        self.nickname = ""
        self.ip = ""
        self.udp_port = -1

class Server:
    def __init__(self):
        self.lock_clients_list = threading.Lock()
        self.clients = []
        self.id = 0
        self.ip = '127.0.0.1'
        self.port = 22222
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen()

    def notify_clients(self, mes_id, new_client):
        with self.lock_clients_list:
            for client in self.clients:
                if len(client.nickname) == 0:
                    continue
                if client._id == new_client._id:
                    #Peerliste
                    if mes_id == 1:
                        continue
                    message = []
                    for x in self.clients:
                        if len(x.nickname) == 0:
                            continue
                        message.append([x.nickname, x.ip, x.udp_port])
                    message = "\n".join(["|".join(y) for y in message])
                    message = message.encode("utf-8")
                    mes_len = len(message).to_bytes(4, byteorder='big')
                    mes_id = (3).to_bytes(1, byteorder='big')
                    outgoing_bytes = mes_len + mes_id + message
                    new_client.socket.sendall(outgoing_bytes)
                else:
                    #Update an Peer: neue Anmeldung
                    combined_str = new_client.nickname + "|" + new_client.ip + "|" + new_client.udp_port
                    body = combined_str.encode('utf-8')
                    mes_len = len(body).to_bytes(4, byteorder='big')
                    mes_id = (mes_id).to_bytes(1, byteorder='big')
                    outgoing_bytes = mes_len + mes_id + body
                    client.socket.sendall(outgoing_bytes)

    def reject_nickname(self, client):
        mes_len = (0).to_bytes(4, byteorder='big')
        mes_id = (5).to_bytes(1, byteorder='big')
        client.socket.sendall(mes_len + mes_id)
        # Verbindung bleibt, oder beenden? Protokollabsprache!

    def send_bad_format(self, client_socket):
        mes_len = (0).to_bytes(4, byteorder='big')
        mes_id = (6).to_bytes(1, byteorder='big')
        client_socket.sendall(mes_len + mes_id)

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
                message = client_socket.recv(message_length).decode("utf-8")
                if not message:
                    break
                local_client = None
                with self.lock_clients_list:
                    for x in self.clients:
                        if x.socket == client_socket and x.addr == addr:
                            local_client = x
                            break
                if message_id == 0:
                    #Anmeldung
                    splits = message.split("|")
                    if len(splits) != 3:
                        self.send_bad_format(client_socket)
                        break
                    if len(splits[0]) > 20 or len(splits[0]) < 1:
                        self.reject_nickname(local_client)
                        continue
                    with self.lock_clients_list:
                        for x in self.clients:
                            if x.nickname == splits[0]:
                                self.reject_nickname(x)
                                continue
                        local_client.nickname = splits[0]
                        local_client.ip = splits[1]
                        local_client.udp_port = splits[2]
                    self.notify_clients(0, local_client)
                elif message_id == 1:
                    #Abmeldung
                    with self.lock_clients_list:
                        self.clients.remove(local_client)
                    self.notify_clients(1, local_client)
                    print(f"{local_client.nickname} disconnected.")
                    break
                elif message_id == 2:
                    #Broadcast
                    with self.lock_clients_list:
                        for x in self.clients:
                            if x != local_client:
                                self.send_broadcast(x, local_client.nickname, message)
                            else:
                                self.send_broadcast(x, local_client.nickname, "Server: Sent your message to everyone: " + message)
                else:
                    self.send_bad_format(client_socket)
                    break

                print(f"Received from {addr}: {message}")
            except Exception as e:
                #print(e)
                break
        client_socket.close()
        # Abmeldung, wenn Verbindung geschlossen wird
        local_client = None
        with self.lock_clients_list:
            for x in self.clients:
                if x.socket == client_socket and x.addr == addr:
                    local_client = x
                    self.clients.remove(local_client)
                    self.notify_clients(1, local_client)
                    print(f"{local_client.nickname} disconnected.")

    """
    0	Anmeldung
	1	Abmeldung
	(uint32_t)(uint8)nickname|ip-Adresse|UDP-Port
	2	Broadcast
	(uint32_t)(uint8)"Nachricht an alle"
    """


    def start_server(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            with self.lock_clients_list:
                self.clients.append(Client_data(self.id, client_socket, addr))
            self.id += 1
            thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
            thread.start()

def main():
    server = Server()
    server.start_server()

main()
