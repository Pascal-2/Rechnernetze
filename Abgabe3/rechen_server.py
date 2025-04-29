import socket
import time
import struct
from functools import reduce

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
                try:
                    # Unpack message (assuming correct format)
                    header = struct.unpack('I3Bb', data_raw[:8])
                    nums_count = header[4]
                    nums = struct.unpack(f'{nums_count}i', data_raw[8:])
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
                    sock.sendto(reply, addr)
                except struct.error as e:
                    print("Struct unpacking failed:", e)
            except socket.timeout:
                print('Server: Socket timed out at', time.asctime())

        sock.close()



    elif type == 'tcp':
        pass
    else:
        exit("invalid type, use udp or tcp. ")

start_server('udp')