import os
import socket
import http.server
import paramiko
from utils import read_in_chunks

class TTC:
    '''
    Telemetry, Tracking & Command module
    '''
    def __init__(self, max_retries):
        # module configuration
        self.BUFFER_SIZE = 1024
        self.MAX_RETRIES = max_retries

        # connection configuration
        self.host_name = socket.gethostname()
        self.port = 65432
        self.ip = socket.gethostbyname(self.host_name)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection = None
        self.addr = None

        print("TT&C module initialized")

    def start(self):
        print("Starting TT&C...")
        self.socket.bind((self.host_name, self.port))
        self.socket.listen()
        print(f"Listening for connections on {self.host_name} ({self.ip})")

    def connect(self):
        self.connection, self.addr = self.socket.accept()
        print(f"Connection established with {self.addr}")

    def send_file(self, file_path, byteorder_length, size, format):
        retries = 0
        
        while retries < self.MAX_RETRIES:
            try:
                # Check if the file path exists
                if not os.path.exists(file_path):
                    print("Error: File path does not exist.")
                    break

                # Check if the file path points to a directory
                if not os.path.isdir(file_path):
                    print("Error: Path does not point to a directory.")
                    break

                file_base_name = os.path.basename(file_path)                
                file_size = os.path.getsize(file_path)
                print("File size is:", file_size, "bytes")
                file_size_in_bytes = file_size.to_bytes(byteorder_length, "big")

                # Sending file size to ground station
                print("Sending the file size")
                self.connection.sendall(file_size_in_bytes)
                msg = self.connection.recv(size).decode(format)
                print("Server:", msg)

                # Send filename of file to ground station
                self.connection.sendall(file_base_name.encode(format))
                print("File name sent")
                msg = self.connection.recv(size).decode(format)
                print("Server:", msg)

                # Send file data
                with open(file_path, "rb") as f:
                    for data in read_in_chunks(f, self.BUFFER_SIZE):
                        self.connection.send(data)
                        
                msg = self.connection.recv(size).decode(format)
                print("Server:", msg)
                break
                
            except OSError as err:
                # Handle operating system error
                print("OS error:", err, "retrying...")
            except ConnectionError as err:
                # Handle connection-related error
                print("Connection error:", err, "retrying...")
            except TimeoutError as err:
                # Handle timeout-related error
                print("Timeout error:", err, "retrying...")
            except socket.error as err:
                # Handle other socket-related errors
                print("Socket error:", err, "retrying...")
            except Exception as err:
                # Handle other general errors
                print("Error occurred:", err, "retrying...")

            retries += 1

        if retries >= self.MAX_RETRIES:
            print("Failed to send file ({}) after {} retries".format(file_path, self.MAX_RETRIES))        