import socket
import threading

# Function to handle a client connection
def handle_client(client_socket, address):
    print(f"Connection from {address} established.")

    while True:
        # Receive data from the client (vehicle)
        data = client_socket.recv(1024)
        if not data:
            break
        
        # Process received data (e.g., parse CAN messages)
        print(f"Received data from {address}: {data.hex()}")

        # Example: Echo back the received data
        client_socket.send(data)

    print(f"Connection from {address} closed.")
    client_socket.close()

# Start the server
def start_server():
    server_host = "127.0.0.1"  # Use "0.0.0.0" to listen on all available interfaces
    server_port = 8888

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_host, server_port))
    server_socket.listen(5)

    print(f"Server listening on {server_host}:{server_port}")

    while True:
        client_socket, address = server_socket.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, address))
        client_handler.start()
