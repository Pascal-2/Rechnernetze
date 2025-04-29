import socket

ssock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # datagram udp

ssock.bind(("127.0.0.1", 50000))

msg, addr = ssock.recvfrom(1000)

print(msg, addr)

print(msg.decode()) # utf-8 decoded

ssock.sendto("Hallo zurück".encode(), addr)

# socket.setdefaultimeout(5)

# -----------------


listen_sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM) # tcp

listen_sock.bind(("127.0.0.1", 50000))

listen_sock.listen(1)

conn, addr=listen_sock.accept()

conn.send(b"Huuuuu")

msg = conn.recv(1000)

msg = conn.recv(1_000_000)

conn.close()

# CurrPorts
# "192.168.1.3", 60000

# -----------------

# tcp socket

# Threads und Net statements für viele Verbindungen auf dem selben Port

tsock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tsock.connect(("127.0.0.1", 50000))
tsock.connect(("192.168.1.3", 60000))
tsock.send(b"Hallo!!!!")
msg = tsock.recv(100)

print(msg.decode())

tsock.send(b"0" * 1_000_000)
tsock.close()


# -----------------------------

testsock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
testsock.connect(("127.0.0.1", 50001))
