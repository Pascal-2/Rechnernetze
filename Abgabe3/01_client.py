import socket

csock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

csock.sendto(b"Hallo", ("127.0.0.1", 50000))

# filter with udp.port==50000

msg, addr = csock.recvfrom(10) # sollte fehler werfen (zu wenig bytes)

msg, addr = csock.recvfrom(100) # fehler Nachricht wurde verworen nach dem fehlerhaften lesen

print(msg.decode()) # sollte hallo zurück

# timeouts setzten kann mit try except abgefangen werden

csock.settimeout(2) # 2 sekunden

