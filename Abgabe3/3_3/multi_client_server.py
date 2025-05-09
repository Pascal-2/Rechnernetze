import socket
import time
import struct
from functools import reduce
import threading


def process_data(raw_data, addr):
    try:
        # Unpack message (assuming correct format)
        header = struct.unpack('I3Bb', raw_data[:8])
        nums_count = header[4]
        nums = struct.unpack(f'{nums_count}i', raw_data[8:])
        full_data = header + nums
        print('received message:', full_data, 'from', addr)
        command = full_data[1:4]
        response = 0
        if command == (83, 85, 77):
            # SUM
            response = sum(nums)

        elif command == (80, 82, 79):
            # PRODUCT
            response = reduce(lambda x, y: x * y, nums)

        elif command == (77, 73, 78):
            # MINIMUM
            response = min([int(x) for x in nums])

        elif command == (77, 65, 88):
            # MAXIMUM
            response = max([int(x) for x in nums])
        else:
            exit("command not found")
        print(response)

        reply = struct.pack('Ii', header[0], response)
        return reply
    except struct.error as e:
        print("Struct unpacking failed:", e)
        exit(1)


def receive(conn, addr):
    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                print('Connection closed from other side')
                return
            reply = process_data(data, addr)
            conn.send(reply)

def listen(sock):
    sock.listen(1)
    print('Listening ...')

    while True:
        try:
            conn, addr = sock.accept()
            threading.Thread(target=receive, args=(conn, addr)).start()
            print('Incoming connection accepted: ', addr)
        except socket.timeout:
            print('Socket timed out listening', time.asctime())

    sock.close()
    if conn:
        conn.close()

def start_server():

    My_IP = '127.0.0.1'
    My_PORT = 50000

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((My_IP, My_PORT))
    print('Listening on Port ', My_PORT, ' for incoming TCP connections')

    listen(sock)


start_server()