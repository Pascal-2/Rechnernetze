import socket
import ssl
import base64
import time

server = "asmtp.htwg-konstanz.de"
port = 587

# Klartext-Verbindung
sock = socket.create_connection((server, port))
print(sock.recv(1024).decode())

# EHLO
sock.sendall(b"EHLO meinclient\r\n")
print(sock.recv(1024).decode())

# STARTTLS korrekt senden
sock.sendall(b"STARTTLS\r\n")
reply = sock.recv(1024).decode()
print(reply)

if not reply.startswith("220"):
    raise Exception("STARTTLS wurde nicht akzeptiert!")

# TLS aktivieren
context = ssl.create_default_context()
ssl_sock = context.wrap_socket(sock, server_hostname=server)

# TLS-EHLO
ssl_sock.sendall(b"EHLO meinclient\r\n")
print(ssl_sock.recv(1024).decode())

# AUTH LOGIN
ssl_sock.sendall(b"AUTH LOGIN\r\n")
print(ssl_sock.recv(1024).decode())

username = base64.b64encode(b"rnetin06").decode()
password = base64.b64encode(b"Ua7toghooPhaiw").decode()

ssl_sock.sendall((username + "\r\n").encode())
print(ssl_sock.recv(1024).decode())

ssl_sock.sendall((password + "\r\n").encode())
print(ssl_sock.recv(1024).decode())

# E-mail senden:

# Absenderadresse (beliebig fälschbar, Achtung!)
ssl_sock.sendall(b"MAIL FROM:<fake@irgendwas.de>\r\n")
print(ssl_sock.recv(1024).decode())

# Empfängeradresse (deine echte Adresse, z.B. Gmail oder HTWG)
ssl_sock.sendall(b"RCPT TO:pa871kai@htwg-konstanz.de\r\n")
print(ssl_sock.recv(1024).decode())

# Beginn des Nachrichtentexts
ssl_sock.sendall(b"DATA\r\n")
print(ssl_sock.recv(1024).decode())

# Nachricht senden (inkl. Header und Body), mit Punkt am Ende
message = """\
From: fake@irgendwas.de <fake@irgendwas.de>
To: Pascal pa871kai@htwg-konstanz.de
Subject: Testmail über SMTP

Hallo! Dies ist ein SMTP-Test mit TLS und Fake-Absender.
"""
ssl_sock.sendall((message + "\r\n.\r\n").encode())
print(ssl_sock.recv(1024).decode())

# Verbindung sauber schließen
ssl_sock.sendall(b"QUIT\r\n")
print(ssl_sock.recv(1024).decode())
