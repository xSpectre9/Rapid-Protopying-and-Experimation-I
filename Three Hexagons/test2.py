import socket

def test_socket_connection(host, port):
    try:
        # Create a socket object
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Connect to the server
            sock.connect((host, port))
            print(f"Successfully connected to {host}:{port}")

            # Send a simple message
            message = "Hello, server!"
            sock.sendall(message.encode('utf-8'))
            print(f"Sent message to server: {message}")

            # Receive the server response
            response = sock.recv(1024)  # Buffer size is 1024 bytes
            print(f"Received from server: {response.decode('utf-8')}")

    except Exception as e:
        print(f"Failed to connect to {host}:{port}")
        print(f"Error: {e}")

# Use the function
test_socket_connection('192.168.40.20', 8142)