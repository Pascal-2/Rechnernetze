import socket
import sys
import time
import random
import struct

for i_id in range(5):
    Server_IP = '127.0.0.1'
    Server_PORT = 50000

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    print('Connecting to TCP server with IP ', Server_IP, ' on Port ', Server_PORT)
    sock.connect((Server_IP, Server_PORT))

    # some random messages to the server
    ops = ["SUM", "PRO", "MIN", "MAX"]
    for i in range(5):
        id = i
        operation = [ord(x) for x in random.choice(ops)]
        nums = random.choices(list(range(5, 15)), k=random.randint(2, 5))
        N = len(nums)
        MESSAGE = struct.pack(f'I3Bb{N}i', id, *operation, N, *nums)
        #print('Client: Sending message', MESSAGE, 'to UDP server with IP ', Server_IP, ' on Port=', Server_PORT)
        print(f"Client: Asking for    {id} {"".join([chr(x) for x in operation])} on {nums}")

        #print('Sending message', MESSAGE)
        sock.send(MESSAGE)
        try:
            msg=sock.recv(1024)
            server_answer = struct.unpack('Ii', msg)
            print(f"Client: received message: ID:{server_answer[0]} RESULT:{server_answer[1]}")
        except socket.timeout:
            print('Socket timed out at',time.asctime())
        except:
            print('Unexpected error:', sys.exc_info()[0])
    sock.close()


