import socket
import time
import struct
import random

Server_IP = '127.0.0.1'
Server_PORT = 50000
id2 = 2
operation2 = [ord(x) for x in "PRO"]
N2 = 2
nums2 = [4,5]
MESSAGE2 = struct.pack(f'I3Bb{len(nums2)}i', id2, *operation2, N2, *nums2)

# some random messages to the server
ops = ["SUM", "PRO", "MIN", "MAX"]
for i in range(20):
    id = i
    operation = [ord(x) for x in random.choice(ops)]
    nums = random.choices(list(range(5, 15)), k=random.randint(2, 5))
    N = len(nums)
    MESSAGE = struct.pack(f'I3Bb{N}i', id, *operation, N, *nums)
    #print('Client: Sending message', MESSAGE, 'to UDP server with IP ', Server_IP, ' on Port=', Server_PORT)
    print(f"Client: Asking for    {id} {"".join([chr(x) for x in operation])} on {nums}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(10)
    sock.sendto(MESSAGE, (Server_IP, Server_PORT))
    try:
        data, addr = sock.recvfrom(1024)
        server_answer = struct.unpack('Ii', data)
        print(f"Client: received message: ID:{server_answer[0]} RESULT:{server_answer[1]} from {addr}")
    except socket.timeout:
        print('Client: Socket timed out at', time.asctime())

    sock.close()



