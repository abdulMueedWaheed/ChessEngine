import socket
import os
import sys
import threading

# Directory to store the shared files
FILES_DIRECTORY = "shared_files"


def handle_UDP_requests(udp_socket, udp_port, tcp_port):
    """Handles UDP discovery requests and responds with server details."""
    while True:
        try:
            data, addr = udp_socket.recvfrom(1024)  # Receive UDP request
            message = data.decode()
            if message.startswith("DISCOVER_SERVER"):
                _, file_path = message.split(" ", 1)  # Parse the file path
                print(f"Received discovery request for file: {file_path} from {addr}")

                # Check if the requested file exists
                file_path_on_server = os.path.join(FILES_DIRECTORY, file_path.strip())
                if os.path.exists(file_path_on_server):
                    file_size = os.path.getsize(file_path_on_server)
                    server_ip = socket.gethostbyname(socket.gethostname())
                    response = f"{server_ip}:{tcp_port} {file_size}"
                    udp_socket.sendto(response.encode(), addr)
                    print(f"File {file_path} found. Responding with server details.")
                else:
                    print(f"File {file_path} not found.")
        except socket.timeout:
            continue  # Ignore timeouts to keep the server running
        except Exception as e:
            print(f"Error handling UDP request: {e}")


def handle_TCP_requests(tcp_socket):
    """Handles TCP file fragment requests from clients."""
    while True:
        try:
            client_socket, client_address = tcp_socket.accept()
            print(f"Accepted connection from {client_address}")
            with client_socket:
                request = client_socket.recv(1024).decode().strip()
                print(f"Received request: {request}")

                # Parse the request (format: GET <file_path> <byte_range>)
                if request.startswith("GET"):
                    _, file_path, byte_range = request.split(" ", 2)
                    start_byte, end_byte = map(int, byte_range.split("-"))
                    print(f"Requested file: {file_path}, Byte range: {start_byte}-{end_byte}")

                    # Serve the requested file fragment
                    file_path_on_server = os.path.join(FILES_DIRECTORY, file_path.strip())
                    if os.path.exists(file_path_on_server):
                        with open(file_path_on_server, "rb") as f:
                            f.seek(start_byte)
                            fragment = f.read(end_byte - start_byte + 1)
                            client_socket.sendall(fragment)
                            print(f"Sent fragment {start_byte}-{end_byte} for {file_path}.")
                    else:
                        print(f"File {file_path} not found.")
                        client_socket.sendall(b"ERROR: File not found.")
                else:
                    print(f"Invalid request format: {request}")
                    client_socket.sendall(b"ERROR: Invalid request format.")
        except Exception as e:
            print(f"Error handling TCP request: {e}")
        finally:
            client_socket.close()


def start_server(udp_port, tcp_port):
    """Starts both UDP and TCP servers."""
    # UDP server for file discovery
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(("", udp_port))
    udp_socket.settimeout(1)  # Set a timeout for UDP socket

    # TCP server for file fragment requests
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(("", tcp_port))
    tcp_socket.listen(5)

    print(f"Server listening on UDP port {udp_port} and TCP port {tcp_port}...")

    # Start UDP request handling in a separate thread
    udp_thread = threading.Thread(target=handle_UDP_requests, args=(udp_socket, udp_port, tcp_port))
    udp_thread.daemon = True
    udp_thread.start()

    # Handle TCP requests in the main thread
    handle_TCP_requests(tcp_socket)


# Default ports
udp_port = 9000
tcp_port = 9001

# Allow a custom directory to be specified via command-line arguments
if len(sys.argv) > 1:
	FILES_DIRECTORY = sys.argv[1]

# Ensure the directory exists
if not os.path.exists(FILES_DIRECTORY):
	os.makedirs(FILES_DIRECTORY)

# Start the server
start_server(udp_port, tcp_port)