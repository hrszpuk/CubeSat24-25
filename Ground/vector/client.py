import socket
import re

HOST = "0.0.0.0"
PORT = 65432
BUFFER_SIZE = 1024
FORMAT = "utf-8"
BYTEORDER_LENGTH = 8

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    try:
        sock.connect((HOST, PORT))
        
    except OSError as err:        
        print("OS error:", err, "retrying...")

        host_input = input("Enter the IP address of the CubeSat: ")

        while not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', host_input):
            print(f"{host_input} is not a valid IP address, try again.")
            host_input = input("Enter the IP address of the CubeSat: ")

        sock.connect((host_input, PORT))

    while True:
        message = input("> ")
        sock.sendall(message.encode(FORMAT))
        response = sock.recv(BUFFER_SIZE).decode(FORMAT)

print("CubeSat:", repr(response))