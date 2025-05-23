import threading
import time
import socket

HOST = '127.0.0.1'  # Server's host
PORT = 22222  # Server's port


class Peer:
    def __init__(self, nickname, ip, udp_port_str):  # udp_port_str is expected as a string
        self.nickname = nickname
        self.ip = ip
        try:
            self.udp_port = int(udp_port_str)  # Store as int
        except ValueError:
            print(f"Error: Invalid UDP port string '{udp_port_str}' for peer {nickname}. Setting port to -1.")
            self.udp_port = -1  # Indicate an invalid port

    def __eq__(self, other):
        if not isinstance(other, Peer):
            return NotImplemented
        return self.ip == other.ip and self.udp_port == other.udp_port and self.nickname == other.nickname

    def __str__(self):
        return f"{self.nickname}:{self.ip}:{self.udp_port}"


class Client:
    def __init__(self, nickname, ip, udp_port, tcp_port_for_initiation):
        self.nickname = nickname
        self.ip = ip
        self.udp_port = udp_port  # This client's UDP port for LISTENING to chat requests
        self.tcp_port_for_initiation = tcp_port_for_initiation  # TCP port THIS client listens on when IT INITIATES a chat

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.peer_list = []
        self.open_chat_sockets = []  # Stores tuples of (socket_object, peer_nickname)
        self.open_chat_sockets_lock = threading.Lock()

    def send_registration(self):
        self.server_client_socket.connect((HOST, PORT))
        # The registration message includes the client's primary UDP listening port
        combined_str = f"{self.nickname}|{self.ip}|{self.udp_port}"
        body = combined_str.encode('utf-8')
        mes_len = len(body).to_bytes(4, byteorder='big')
        mes_id = (0).to_bytes(1, byteorder='big')  # Registration ID
        outgoing_bytes = mes_len + mes_id + body
        self.server_client_socket.sendall(outgoing_bytes)
        print(f"[{self.nickname}] Registration sent to server.")

    def new_peer_update(self, message):
        splits = message.split("|")
        if len(splits) != 3:
            print(f"[{self.nickname}] Malformed new peer update: {message}")
            return
        peer = Peer(splits[0], splits[1], splits[2])
        if peer.udp_port != -1:
            if peer.nickname == self.nickname:  # Don't add self to peer list
                return
            if peer not in self.peer_list:
                self.peer_list.append(peer)
                print(f"[{self.nickname}] Added new peer: {peer}")
        else:
            print(f"[{self.nickname}] Failed to add peer from update due to invalid port: {message}")

    def del_peer_update(self, message):
        splits = message.split("|")
        if len(splits) != 3:
            print(f"[{self.nickname}] Malformed peer delete update: {message}")
            return
        peer_to_remove = Peer(splits[0], splits[1], splits[2])
        if peer_to_remove.udp_port != -1:
            try:
                self.peer_list.remove(peer_to_remove)
                print(f"[{self.nickname}] Removed peer: {peer_to_remove}")
            except ValueError:
                print(f"[{self.nickname}] Tried to remove peer not in list: {peer_to_remove}")
        else:
            print(f"[{self.nickname}] Failed to process peer delete due to invalid port in message: {message}")

    def receive_broadcast(self, message):
        splits = message.split("|")
        if len(splits) != 2:  # Expected: sender_nickname|broadcast_message
            print(f"[{self.nickname}] Malformed broadcast message: {message}")
            return
        # Prompt user again after printing broadcast to keep input line clean
        print(f"\nBroadcast from {splits[0]}:\n\"{splits[1]}\"\n[{self.nickname}] Your input: ", end='')

    def initialize_peer_list(self, message):
        self.peer_list = []  # Clear before initializing
        if message:
            lines = message.split("\n")
            for line in lines:
                if not line.strip(): continue
                splits = line.split("|")
                if len(splits) == 3:
                    peer = Peer(splits[0], splits[1], splits[2])
                    if peer.udp_port != -1:
                        if peer.nickname == self.nickname: continue  # Don't add self
                        if peer not in self.peer_list:
                            self.peer_list.append(peer)
                else:
                    print(f"[{self.nickname}] Malformed line in peer list init: {line}")
            print(f"[{self.nickname}] Peer list initialized with {len(self.peer_list)} peer(s).")
        else:
            print(f"[{self.nickname}] Initial peer list from server is empty.")

    def send_broadcast(self, message_text):
        # Server will know sender from connection; client sends only the message content
        body = message_text.encode('utf-8')
        mes_len = len(body).to_bytes(4, byteorder='big')
        mes_id = (2).to_bytes(1, byteorder='big')  # Broadcast ID
        outgoing_bytes = mes_len + mes_id + body
        try:
            self.server_client_socket.sendall(outgoing_bytes)
        except Exception as e:
            print(f"[{self.nickname}] Failed to send broadcast to server: {e}")

    def handle_bad_format_response(self):
        print(f"[{self.nickname}] Received 'bad format' response from server. Closing connection.")
        self.close_server_connection()

    def handle_refused_registration(self):
        print(f"[{self.nickname}] Server refused registration. Nickname might be invalid or taken.")
        print(f"[{self.nickname}] Please disconnect ('d') and try registering again with a different nickname.")
        self.close_server_connection()

    def log_out(self):
        print(f"[{self.nickname}] Sending log out message to server.")
        # The logout message identifies the client by its registration details
        combined_str = f"{self.nickname}|{self.ip}|{self.udp_port}"
        body = combined_str.encode('utf-8')
        mes_len = len(body).to_bytes(4, byteorder='big')
        mes_id = (1).to_bytes(1, byteorder='big')  # Logout ID
        outgoing_bytes = mes_len + mes_id + body
        try:
            self.server_client_socket.sendall(outgoing_bytes)
        except Exception as e:
            print(f"[{self.nickname}] Failed to send log out message: {e}")
        # Regardless of send success, proceed to close connection
        self.close_all_connections()

    def close_server_connection(self):
        print(f"[{self.nickname}] Closing connection to server.")
        try:
            self.server_client_socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass  # Socket might already be closed or not connected
        finally:
            self.server_client_socket.close()

    def close_all_connections(self):
        self.close_server_connection()
        with self.open_chat_sockets_lock:
            for s, peer_nick in self.open_chat_sockets:
                print(f"[{self.nickname}] Closing chat socket with {peer_nick}.")
                try:
                    s.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                finally:
                    s.close()
            self.open_chat_sockets = []
        try:
            self.udp_socket.close()  # Close UDP listening socket
            print(f"[{self.nickname}] UDP socket closed.")
        except OSError:
            pass

    def handle_server_messages(self):
        try:
            while True:  # TODO: Add a flag to break this loop on client shutdown
                header = self.server_client_socket.recv(5)  # Length (4 bytes) + ID (1 byte)
                if not header:
                    print(f"[{self.nickname}] Server connection closed (no header received).")
                    break

                message_length = int.from_bytes(header[:4], byteorder='big', signed=False)
                message_id = int.from_bytes(header[4:], byteorder='big', signed=False)

                message_body = ""
                if message_length > 0:
                    message_body_bytes = self.server_client_socket.recv(message_length)
                    if not message_body_bytes and message_length > 0:
                        print(f"[{self.nickname}] Server connection closed while reading message body.")
                        break
                    message_body = message_body_bytes.decode("utf-8")

                if message_id == 0:
                    self.new_peer_update(message_body)
                elif message_id == 1:
                    self.del_peer_update(message_body)
                elif message_id == 2:
                    self.receive_broadcast(message_body)
                elif message_id == 3:
                    self.initialize_peer_list(message_body)
                elif message_id == 5:
                    self.handle_refused_registration(); break  # Stop after refusal
                elif message_id == 6:
                    self.handle_bad_format_response(); break  # Stop after bad format
                else:
                    print(f"[{self.nickname}] Unknown message ID {message_id} from server. Body: '{message_body}'")

        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as e:
            print(f"[{self.nickname}] Connection to server lost: {e}")
        except socket.error as e:
            print(f"[{self.nickname}] Socket error with server: {e}")
        except Exception as e:
            print(f"[{self.nickname}] Unexpected error handling server messages: {type(e).__name__} {e}")
        finally:
            print(f"[{self.nickname}] Server message handling thread stopped.")
            self.close_server_connection()  # Ensure server socket is closed if loop exits

    def change_username(self, new_nickname_with_quotes):
        # This function only changes nickname locally.
        # For server-side change, client needs to re-register.
        new_nickname = new_nickname_with_quotes.strip('"')
        if not (1 <= len(new_nickname) <= 20 and "|" not in new_nickname):
            print(f"[{self.nickname}] Invalid new nickname format: '{new_nickname}'. Not changed.")
            return
        print(
            f"[{self.nickname}] Local nickname changed to '{new_nickname}'. This does NOT re-register with the server.")
        self.nickname = new_nickname

    def initiate_peer_chat(self, target_peer_nickname):
        initiator_listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # This client (initiator) binds to ITS OWN self.tcp_port_for_initiation
            # It will tell the other peer to connect to this port.
            initiator_listener_socket.bind((self.ip, self.tcp_port_for_initiation))
        except OSError as e:
            print(
                f"[{self.nickname}] Error binding to {self.ip}:{self.tcp_port_for_initiation} for initiating chat: {e}")
            print(
                f"[{self.nickname}] This port might be in use. Ensure client's tcp_port_for_initiation is unique or free.")
            initiator_listener_socket.close()
            return

        initiator_listener_socket.listen(1)
        print(
            f"[{self.nickname}] Initiator listening on {self.ip}:{self.tcp_port_for_initiation} for {target_peer_nickname} to connect.")

        target_peer = None
        for p in self.peer_list:
            if p.nickname == target_peer_nickname:
                target_peer = p
                break

        if not target_peer or target_peer.udp_port == -1:
            print(f"[{self.nickname}] Could not find valid peer '{target_peer_nickname}' in peer list.")
            initiator_listener_socket.close()
            return

        # Message to peer: MyNickname | MyIP | MyTCPPortForYouToConnectTo
        request_str = f"{self.nickname}|{self.ip}|{self.tcp_port_for_initiation}"
        request_body = request_str.encode('utf-8')
        request_len_bytes = len(request_body).to_bytes(4, byteorder='big')
        request_id_bytes = (4).to_bytes(1, byteorder='big')  # P2P Chat Request ID
        udp_request_packet = request_len_bytes + request_id_bytes + request_body

        connected_data_socket = None
        for attempt in range(2):
            print(
                f"[{self.nickname}] Sending UDP chat request to {target_peer.nickname} ({target_peer.ip}:{target_peer.udp_port}), attempt {attempt + 1}/2.")
            print(f"[{self.nickname}] Requesting they connect to my TCP port: {self.tcp_port_for_initiation}.")
            self.udp_socket.sendto(udp_request_packet, (target_peer.ip, target_peer.udp_port))
            try:
                initiator_listener_socket.settimeout(7.0)  # Timeout for this accept() attempt
                connected_data_socket, addr = initiator_listener_socket.accept()
                print(f"[{self.nickname}] Accepted TCP connection from {addr} for chat with {target_peer.nickname}.")
                break
            except socket.timeout:
                print(
                    f"[{self.nickname}] Timeout waiting for {target_peer.nickname} to connect (attempt {attempt + 1}/2).")
                if attempt == 1:  # Last attempt
                    print(f"[{self.nickname}] Failed to establish TCP connection with {target_peer.nickname}.")
                    initiator_listener_socket.close()
                    return
            except Exception as e:
                print(f"[{self.nickname}] Error on accept() for {target_peer.nickname}: {e}")
                initiator_listener_socket.close()
                return

        initiator_listener_socket.close()  # Close listener socket, we have the data_socket or failed

        if not connected_data_socket:
            return  # Failed to connect

        connected_data_socket.settimeout(None)  # Make socket blocking for chat

        with self.open_chat_sockets_lock:
            if any(s_info[1] == target_peer.nickname for s_info in self.open_chat_sockets):
                print(f"[{self.nickname}] Chat with {target_peer.nickname} already exists. Closing new connection.")
                connected_data_socket.close()
                return
            self.open_chat_sockets.append((connected_data_socket, target_peer.nickname))

        chat_handler_thread = threading.Thread(target=self.chat_with_peer, args=(target_peer.nickname,))
        chat_handler_thread.daemon = True
        chat_handler_thread.start()
        print(f"[{self.nickname}] Chat session with {target_peer.nickname} (initiated by us) started.")

    def chat_with_peer(self, peer_nickname):
        peer_tcp_socket = None
        with self.open_chat_sockets_lock:  # Find the correct socket
            for sock_info in self.open_chat_sockets:
                if sock_info[1] == peer_nickname:
                    peer_tcp_socket = sock_info[0]
                    break

        if peer_tcp_socket is None:
            print(f"[{self.nickname}] Internal Error: Could not find TCP socket for peer {peer_nickname}.")
            return

        print(f"[{self.nickname}] Listening for messages from {peer_nickname}.")
        try:
            while True:  # TODO: Add flag to break loop on client shutdown
                # Correctly read from the peer_tcp_socket
                header = peer_tcp_socket.recv(5)  # Length (4) + ID (1)
                if not header:
                    print(f"[{self.nickname}] Connection with {peer_nickname} closed (no header).")
                    break

                message_length = int.from_bytes(header[:4], byteorder='big', signed=False)
                message_id = int.from_bytes(header[4:], byteorder='big', signed=False)

                message_body_str = ""
                if message_length > 0:
                    message_body_bytes = peer_tcp_socket.recv(message_length)
                    if not message_body_bytes and message_length > 0:
                        print(f"[{self.nickname}] Connection with {peer_nickname} closed (no body).")
                        break
                    message_body_str = message_body_bytes.decode("utf-8")

                if message_id == 4:  # P2P message ID
                    print(f"\nMessage from {peer_nickname}: {message_body_str}\n[{self.nickname}] Your input: ", end='')
                else:
                    print(
                        f"[{self.nickname}] Received unexpected message ID {message_id} from {peer_nickname}. Content: '{message_body_str}'")

        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError) as e:
            print(f"[{self.nickname}] Connection with {peer_nickname} lost: {e}")
        except socket.error as e:  # Other socket errors
            print(f"[{self.nickname}] Socket error with {peer_nickname}: {e}")
        except Exception as e:
            print(f"[{self.nickname}] Error in chat_with_peer with {peer_nickname}: {type(e).__name__} {e}")
        finally:
            print(f"[{self.nickname}] Ending chat receiver thread for {peer_nickname}.")
            with self.open_chat_sockets_lock:
                self.open_chat_sockets = [s_info for s_info in self.open_chat_sockets if s_info[0] != peer_tcp_socket]
            try:
                peer_tcp_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            finally:
                peer_tcp_socket.close()

    def menu_options(self):
        print(
            "\nClient menu options:\n    'p' - See peer list\n    'b' - Send broadcast to all peers (via server)\n    'n' - Initiate a new peer-to-peer chat\n    'm' - Message a peer in an open P2P chat\n    'c' - Change local nickname (no server update)\n    'd' - Disconnect and quit")
        while True:
            user_input = input(f"[{self.nickname}] Your input: ").strip()

            if not user_input: continue

            if user_input == "p":
                if self.peer_list:
                    print(f"[{self.nickname}] Online Peers:\n" + "\n".join([str(p) for p in self.peer_list]))
                else:
                    print(f"[{self.nickname}] No peers currently online or list not yet received.")

            elif user_input == "b":
                message_input = input("Enter broadcast message: ")
                if message_input: self.send_broadcast(message_input)

            elif user_input == "d":
                print(f"[{self.nickname}] Disconnecting...")
                self.log_out()  # This now calls close_all_connections
                break  # Exit menu loop, leading to program termination

            elif user_input == "n":
                if not self.peer_list:
                    print(f"[{self.nickname}] Peer list is empty. Cannot initiate chat.")
                    continue
                print(f"Available peers for chat:\n" + "\n".join([p.nickname for p in self.peer_list]))
                peer_to_chat_with = input("Enter nickname of peer to chat with: ")

                is_valid_target = any(p.nickname == peer_to_chat_with for p in self.peer_list)
                if not is_valid_target:
                    print(f"[{self.nickname}] Peer '{peer_to_chat_with}' not found in your peer list.")
                    continue

                with self.open_chat_sockets_lock:
                    if any(s_info[1] == peer_to_chat_with for s_info in self.open_chat_sockets):
                        print(f"[{self.nickname}] You are already in a chat with {peer_to_chat_with}.")
                        continue
                self.initiate_peer_chat(peer_to_chat_with)

            elif user_input == "m":
                if not self.open_chat_sockets:
                    print(f"[{self.nickname}] No open P2P chats. Use 'n' to start one.")
                    continue
                print(f"Open chats with: " + ", ".join([s_info[1] for s_info in self.open_chat_sockets]))
                peer_to_message = input("Enter nickname of peer to send message to: ")

                target_socket = None
                with self.open_chat_sockets_lock:
                    for s, nick in self.open_chat_sockets:
                        if nick == peer_to_message:
                            target_socket = s
                            break

                if target_socket:
                    message_to_peer = input(f"Enter message for {peer_to_message}: ")
                    body = message_to_peer.encode('utf-8')
                    mes_len_bytes = len(body).to_bytes(4, byteorder='big')
                    mes_id_bytes = (4).to_bytes(1, byteorder='big')  # P2P message ID
                    try:
                        target_socket.sendall(mes_len_bytes + mes_id_bytes + body)
                        print("Message sent.")
                    except (BrokenPipeError, ConnectionResetError) as e:
                        print(f"[{self.nickname}] Connection lost while sending to {peer_to_message}: {e}")
                        # The chat_with_peer thread for this peer should handle cleanup.
                    except Exception as e:
                        print(f"[{self.nickname}] Error sending message to {peer_to_message}: {e}")
                else:
                    print(f"[{self.nickname}] No open chat found with '{peer_to_message}'.")

            elif user_input == "c":  # Change local nickname
                new_name_input = input("Enter new nickname (e.g., \"new_name\"): ")
                self.change_username(new_name_input)

            else:
                print(f"[{self.nickname}] Unknown command. Type 'd' to disconnect and quit.")

            # time.sleep(0.1) # Generally not needed as input() is blocking

    def accept_peer_chat(self, initiator_nickname, initiator_ip, initiator_tcp_port):
        print(
            f"[{self.nickname}] Received chat request from {initiator_nickname} ({initiator_ip}:{initiator_tcp_port}). Attempting to connect back.")

        # This client (acceptor) creates a socket to CONNECT to the initiator's listening port
        acceptor_tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            acceptor_tcp_socket.settimeout(10)
            acceptor_tcp_socket.connect((initiator_ip, initiator_tcp_port))
            print(
                f"[{self.nickname}] Successfully connected to {initiator_nickname} at {initiator_ip}:{initiator_tcp_port}.")
        except socket.timeout:
            print(f"[{self.nickname}] Timeout connecting back to {initiator_nickname}.")
            acceptor_tcp_socket.close()
            return
        except ConnectionRefusedError:
            print(f"[{self.nickname}] Connection refused by {initiator_nickname}. They might not be listening anymore.")
            acceptor_tcp_socket.close()
            return
        except Exception as e:
            print(f"[{self.nickname}] Error connecting to {initiator_nickname}: {e}")
            acceptor_tcp_socket.close()
            return

        acceptor_tcp_socket.settimeout(None)  # Make socket blocking for chat

        with self.open_chat_sockets_lock:
            if any(s_info[1] == initiator_nickname for s_info in self.open_chat_sockets):
                print(f"[{self.nickname}] Chat with {initiator_nickname} already exists. Closing redundant connection.")
                acceptor_tcp_socket.close()
                return
            self.open_chat_sockets.append((acceptor_tcp_socket, initiator_nickname))

        # Start a thread to handle receiving messages from this peer
        chat_handler_thread = threading.Thread(target=self.chat_with_peer, args=(initiator_nickname,))
        chat_handler_thread.daemon = True
        chat_handler_thread.start()
        print(f"[{self.nickname}] Chat session with {initiator_nickname} (they initiated) established.")

    def handle_udp_chat_requests(self):
        try:
            self.udp_socket.bind((self.ip, self.udp_port))
            print(f"[{self.nickname}] UDP listener started on {self.ip}:{self.udp_port} for P2P chat requests.")
        except OSError as e:
            print(f"[{self.nickname}] CRITICAL: Failed to bind UDP socket to {self.ip}:{self.udp_port}: {e}")
            print(f"[{self.nickname}] This client will not be able to receive P2P chat initiations.")
            return

        while True:  # TODO: Add flag to break loop on client shutdown
            try:
                # Correctly parse the incoming UDP packet
                data, addr = self.udp_socket.recvfrom(2048)  # Max expected UDP packet size

                if len(data) < 5:  # Minimum: 4 bytes for length, 1 byte for ID
                    print(
                        f"[{self.nickname}] Received too short UDP packet ({len(data)} bytes) from {addr}. Discarding.")
                    continue

                msg_body_len = int.from_bytes(data[0:4], byteorder='big', signed=False)
                msg_id = int.from_bytes(data[4:5], byteorder='big', signed=False)

                expected_total_len = 4 + 1 + msg_body_len
                if len(data) != expected_total_len:
                    print(
                        f"[{self.nickname}] UDP packet from {addr} has mismatched length. Header says body {msg_body_len}B (total {expected_total_len}B), got {len(data)}B. Discarding.")
                    continue

                if msg_id == 4:  # P2P Chat Request ID
                    message_body_str = data[5: 5 + msg_body_len].decode('utf-8')
                    splits = message_body_str.split("|")  # InitiatorNickname | InitiatorIP | InitiatorTCPPort

                    if len(splits) == 3:
                        req_peer_nick, req_peer_ip, req_peer_tcp_port_str = splits
                        print(
                            f"[{self.nickname}] Received P2P chat UDP request from {req_peer_nick} ({req_peer_ip}:{req_peer_tcp_port_str}) (source UDP: {addr}).")

                        try:
                            req_peer_tcp_port = int(req_peer_tcp_port_str)
                        except ValueError:
                            print(
                                f"[{self.nickname}] Invalid TCP port '{req_peer_tcp_port_str}' in chat request from {req_peer_nick}. Discarding.")
                            continue

                        with self.open_chat_sockets_lock:  # Avoid race condition if already chatting
                            if any(s_info[1] == req_peer_nick for s_info in self.open_chat_sockets):
                                print(
                                    f"[{self.nickname}] Already in chat with {req_peer_nick}. Ignoring new UDP request.")
                                continue

                        # Start a new thread to connect back to the initiator
                        accept_thread = threading.Thread(target=self.accept_peer_chat,
                                                         args=(req_peer_nick, req_peer_ip, req_peer_tcp_port))
                        accept_thread.daemon = True
                        accept_thread.start()
                    else:
                        print(
                            f"[{self.nickname}] Malformed P2P chat request body from {addr}: '{message_body_str}'. Expected 3 parts, got {len(splits)}.")
                else:
                    print(
                        f"[{self.nickname}] Received UDP packet from {addr} with non-P2P-request ID {msg_id}. Discarding.")

            except socket.timeout:
                continue
            except ConnectionResetError as e:  # Windows specific for UDP when ICMP port unreachable is received
                print(
                    f"[{self.nickname}] UDP ConnectionResetError (e.g. ICMP Port Unreachable from {addr if 'addr' in locals() else 'unknown'}): {e}. Continuing.")
            except OSError as e:  # Socket closed, e.g. during shutdown
                print(f"[{self.nickname}] OSError in UDP listener (socket likely closed, exiting loop): {e}")
                break
            except Exception as e:
                print(f"[{self.nickname}] Unexpected error in handle_udp_chat_requests: {type(e).__name__} {e}")
                time.sleep(0.1)  # Prevent rapid spinning on persistent unknown error
        print(f"[{self.nickname}] UDP listener thread stopped.")

    def start_client(self):
        print(f"[{self.nickname}] Starting client...")
        try:
            self.send_registration()
        except Exception as e:
            print(f"[{self.nickname}] Failed to connect or send initial registration to server {HOST}:{PORT}: {e}")
            print(f"[{self.nickname}] Please ensure the server is running and accessible. Exiting client.")
            self.close_all_connections()  # Clean up any partially opened sockets
            return

        server_thread = threading.Thread(target=self.handle_server_messages)
        server_thread.daemon = True
        server_thread.start()

        udp_thread = threading.Thread(target=self.handle_udp_chat_requests)
        udp_thread.daemon = True
        udp_thread.start()

        # Menu thread is not daemon, so main program waits for it.
        menu_thread = threading.Thread(target=self.menu_options)
        menu_thread.start()

        menu_thread.join()  # Wait for user to quit via menu

        print(f"[{self.nickname}] Menu exited. Shutting down other components...")
        # log_out() in menu_options calls close_all_connections(), which should handle socket cleanup.
        # Daemon threads will exit once the main thread (this one) finishes.
        print(f"[{self.nickname}] Client shutdown complete.")


def main():
    while True:
        username = input("Please enter your nickname (1-20 chars, no '|'): ").strip()
        if 1 <= len(username) <= 20 and "|" not in username:
            break
        else:
            print("Invalid nickname. Please try again.")

    my_ip = "127.0.0.1"  # For local testing. For wider network, use actual interface IP.

    # Allow different ports for multiple local instances
    # This is a simple way; for production, port assignment might be dynamic or configured.
    instance_num_str = input("Enter instance number (e.g., 1 or 2) for unique port assignment: ").strip()
    try:
        instance_num = int(instance_num_str)
        if instance_num < 1: raise ValueError
    except ValueError:
        print("Invalid instance number. Defaulting to 1.")
        instance_num = 1

    # Base ports - ensure these don't clash with other apps or server
    base_udp_port = 33330
    base_tcp_port_initiation = 23230

    my_udp_port = base_udp_port + instance_num  # For listening to P2P chat requests
    my_tcp_port_for_initiation = base_tcp_port_initiation + instance_num  # For listening when this client initiates

    client_instance = Client(username, my_ip, my_udp_port, my_tcp_port_for_initiation)
    client_instance.start_client()


if __name__ == '__main__':
    main()