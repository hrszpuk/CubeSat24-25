import os
import socket
from datetime import datetime
from TTC.utils import read_in_chunks, get_connection_info

class TTC:
    def __init__(self, log_queue, ip="0.0.0.0", port=65432, buffer_size=1024, format="utf-8", byteorder_length=8, max_retries=3):
        log_queue.put(("TT&C", "Initializing..."))

        # module configuration
        self.log_queue = log_queue
        self.BUFFER_SIZE = buffer_size
        self.FORMAT = format
        self.BYTEORDER_LENGTH = byteorder_length
        self.MAX_RETRIES = max_retries

        # connection configuration
        self.host_name = socket.gethostname()
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection = None
        self.connection_addr = None
        self.last_command_received = None

        log_queue.put(("TT&C", "Initialized"))

    def log(self, msg):
        self.log_queue.put(("TT&C", msg))

    def start(self):
        self.log("Starting subsystem...")
        self.socket.bind((self.ip, self.port))
        self.socket.listen()
        self.log(f"Listening for connections on {self.host_name} ({self.ip}:{self.port})")

    def connect(self):
        self.connection, self.connection_addr = self.socket.accept()
        self.log(f"Connection established with {self.connection_addr}")

    def get_connection(self):
        return self.connection

    def get_status(self):
        self.log("Getting subsystem status...")
        status = {}
        connection_info = get_connection_info()

        for metric, value in connection_info:
            if value is not None:
                item_str = f"{value}"

                if "Frequency" in metric:
                    item_str += " GHz"
                elif metric == "Signal Strength":
                    item_str += " dBm"
                elif metric == "Data Transmission Rate":
                    item_str += " Mb/s"
            else:
                item_str = None
            
            status[metric] = item_str

        status["Last Command Received"] = self.last_command_received
        self.log(f"Subsystem status: {status}")
        return status

    def await_message(self):
        while True:
            msg = self.connection.recv(self.BUFFER_SIZE).decode(self.FORMAT)

            if not msg:
                self.log(f"Connection with {self.connection_addr} dropped")
                self.connection = None
                self.connection_addr = None
                break

            self.last_command_received = datetime.now()
            self.log(f"[{self.last_command_received}] CubeSat received: {msg}")
            self.connection.sendall(msg)
            self.process_command(msg)

    def process_command(self, msg):
        self.log("Processing command...")
        tokens = msg.split(" ")
        command = tokens[0]
        self.log(f"Command: {command}")
        arguments = tokens[1:]
        self.log(f"Arguments: {arguments}")

        match command:
            case "start_phase":
                pass
            case "shutdown":
                pass
            case _:
                self.log(f"[ERROR] Invalid command: {command}")
                self.connection.sendall(f"[ERROR] {command} is not a valid command!".encode(self.FORMAT))


    def send_file(self, file_path):
        retries = 0
        
        while retries < self.MAX_RETRIES:
            self.log(f"Attempt {retries} to send file {file_path}...")
            try:
                if not os.path.exists(file_path):
                    self.log(f"[ERROR] {file_path} does not exist!")
                    break

                if not os.path.isdir(file_path):
                    self.log(f"[ERROR] {file_path} does not point to a directory!")
                    break

                file_base_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                file_size_in_bytes = file_size.to_bytes(self.BYTEORDER_LENGTH, "big")
                self.connection.sendall(file_size_in_bytes)
                self.log("Sent file size")
                self.connection.sendall(file_base_name.encode(self.FORMAT))
                self.log("Sent file name")

                with open(file_path, "rb") as f:
                    for data in read_in_chunks(f, self.BUFFER_SIZE):
                        self.connection.send(data)

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
            self.log(f"[ERROR] Failed to send file {file_path} after {self.MAX_RETRIES} retries!")        