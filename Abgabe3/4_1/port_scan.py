import socket
import time
from threading import Thread


def ask_this_port(port):
    global port_set
    MESSAGE = f'Hello, World! Port: {Server_PORT}'

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    print('Connecting to TCP server with IP ', Server_IP, ' on Port ', Server_PORT)
    try:
        sock.connect((Server_IP, Server_PORT))
        port_set.add(Server_PORT)
        print('Sending message', MESSAGE)
        sock.send(MESSAGE.encode('utf-8'))
        try:
            msg = sock.recv(1024).decode('utf-8')
            print('Message received(TCP): ', msg, "Port: ", port)
        except socket.timeout:
            print('Socket timed out at', time.asctime())
        sock.close()
    except socket.error as e:
        print(e)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(10)
        sock.sendto(MESSAGE.encode('utf-8'), (Server_IP, Server_PORT))
        try:
            data, addr = sock.recvfrom(1024)
            if data:
                port_set.add(Server_PORT)
            print('received message: ' + data.decode('utf-8') + ' from ', addr, "Port: ", port)
        except socket.timeout:
            print('Socket timed out at', time.asctime())

        sock.close()
    except socket.error as e:
        print(e)

def ask_with_less_print(Server_PORT):
    global port_set
    my_info_for_main = ""
    MESSAGE = f'Hello, World! Port: {Server_PORT}'

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    try:
        sock.connect((Server_IP, Server_PORT))
        port_set.add(Server_PORT)
        my_info_for_main = 'Open Port(TCP): ' + str(Server_PORT)
        sock.send(MESSAGE.encode('utf-8'))
        try:
            msg = sock.recv(1024).decode('utf-8')
            my_info_for_main += ' | Message received(TCP): ' + msg
        except socket.timeout:
            #print('Socket timed out at', time.asctime())
            my_info_for_main += ' timeout(TCP)'
        sock.close()
    except socket.error as e:
        my_info_for_main += str(e) + '(TCP)'

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(10)
        sock.sendto(MESSAGE.encode('utf-8'), (Server_IP, Server_PORT))
        try:
            data, addr = sock.recvfrom(1024)
            if data:
                port_set.add(Server_PORT)
                my_info_for_main += ' | received message(UDP): ' + data.decode('utf-8') + ' from ' + str(addr) + "Port: " + str(Server_PORT)
            else:
                my_info_for_main += ' no data(UDP) '
        except socket.timeout:
            #print('Socket timed out at', time.asctime())
            my_info_for_main += ' timeout(UDP)'

        sock.close()
    except socket.error as e:
        my_info_for_main += str(e)
    thread_texts[Server_PORT - 1] = my_info_for_main

Server_IP = '141.37.168.26'   #'127.0.0.1'
port_set = set()
threads = []
thread_texts = [""] * 50
for Server_PORT in range(1, 51):
    t = Thread(target= ask_with_less_print, args = (Server_PORT,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()
print("number of ports we were able to connect to: ", len(port_set))
for i in range(len(thread_texts)):
    print('Port_', i + 1, thread_texts[i])
