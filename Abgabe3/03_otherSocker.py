import socket

sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.sendto(b"Hallo 2", ("127.0.0.1", 52400))