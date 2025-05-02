import socket
import time
import struct
from functools import reduce

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


def start_server(type):
    if type == 'udp':

        My_IP = "127.0.0.1"
        My_PORT = 50000
        server_activity_period = 20  # Zeit, wie lange der Server aktiv sein soll

        sock = socket.socket(socket.AF_INET,
                             socket.SOCK_DGRAM)
        sock.bind((My_IP, My_PORT))

        sock.settimeout(10)
        t_end = time.time() + server_activity_period  # Ende der Aktivitätsperiode

        while time.time() < t_end:
            try:
                data_raw, addr = sock.recvfrom(1024)
                reply = process_data(data_raw, addr)
                sock.sendto(reply, addr)
            except socket.timeout:
                print('Server: Socket timed out at', time.asctime())

        sock.close()



    elif type == 'tcp':
        My_IP = '127.0.0.1'
        My_PORT = 50000
        server_activity_period = 30

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((My_IP, My_PORT))
        print('Listening on Port ', My_PORT, ' for incoming TCP connections')

        t_end = time.time() + server_activity_period  # Ende der Aktivitätsperiode

        sock.listen(1)
        print('Listening ...')

        while time.time() < t_end:
            try:
                conn, addr = sock.accept()
                print('Incoming connection accepted: ', addr)
                break
            except socket.timeout:
                print('Socket timed out listening', time.asctime())

        while time.time() < t_end:
            try:
                data = conn.recv(1024)
                if not data:  # receiving empty messages means that the socket other side closed the socket
                    print('Connection closed from other side')
                    print('Closing ...')
                    conn.close()
                    break
                reply = process_data(data, addr)
                conn.send(reply)
            except socket.timeout:
                print('Socket timed out at', time.asctime())

        sock.close()
        if conn:
            conn.close()

    else:
        exit("invalid type, use udp or tcp. ")

start_server('tcp')