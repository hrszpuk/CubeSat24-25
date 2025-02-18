import os
import socket
import http
# import paramiko

def read_in_chunks(file_object, chunk_size = 1024):
    while True:
        data = file_object.read(chunk_size)

        if not data:
            break

        yield data

class TTCModule:
    '''
    Telemetry, Tracking & Command module
    '''
    def __init__(self, max_retries):
        # module instantiation configuration
        self.max_retries = max_retries

        # initiate connection
        self.client_hostname = socket.gethostname()
        self.client_ip = socket.gethostbyname(self.client_hostname)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def send_file(self, file_path, byteorder_length, size, format):
        retries = 0
        
        while retries < self.max_retries:
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
                self.client.sendall(file_size_in_bytes)
                msg = self.client.recv(size).decode(format)
                print("Server:", msg)

                # Send filename of file to ground station
                self.client.sendall(file_base_name.encode(format))
                print("File name sent")
                msg = self.client.recv(size).decode(format)
                print("Server:", msg)

                # Send file data
                with open(file_path, "rb") as f:
                    for data in read_in_chunks(f, 1024):
                        self.client.send(data)
                        
                msg = self.client.recv(size).decode(format)
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

        if retries == self.max_retries:
            print("Failed to send file ({}) after {} retries".format(file_path, self.max_retries))        