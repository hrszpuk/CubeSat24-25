import socket

HOST = "0.0.0.0"
PORT = 65432
BUFFER_SIZE = 1024

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((HOST, PORT))

    while True:
        message = input("> ")
        sock.sendall(message.encode("UTF-8"))
        response = sock.recv(BUFFER_SIZE)

print("Client received", repr(response))