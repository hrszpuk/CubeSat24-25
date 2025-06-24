import os
import socket
import asyncio
import websockets
import json
from enum import Enum
from datetime import datetime
from TTC.utils import get_connection_info

State = Enum("State", [("INITIALIZING", 0), ("READY", 1), ("CONNECTED", 2)])
MessageType = Enum("MessageType", [("MESSAGE", 0), ("FILEMETADATA", 1), ("FILEDATA", 2)])

class TTC:
    def __init__(self, pipe, log_queue, port=80, buffer_size=1024, format="utf-8", byteorder_length=8, max_retries=3):
        log_queue.put(("TT&C", "Initializing..."))
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 0))

        # module configuration
        self.state = State.INITIALIZING
        self.pipe = pipe
        self.log_queue = log_queue
        self.BUFFER_SIZE = buffer_size
        self.FORMAT = format
        self.BYTEORDER_LENGTH = byteorder_length
        self.MAX_RETRIES = max_retries

        # connection configuration
        self.host_name = socket.gethostname()
        self.ip = s.getsockname()[0]
        self.port = port
        self.connection = None
        self.last_command_received = None

        log_queue.put(("TT&C", "Initialized"))

    def log(self, msg):
        print(msg)
        self.log_queue.put(("TT&C", msg))
    
    def start(self):
        self.log("Starting subsystem...")
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(self.start_server())
        event_loop.run_forever()

    async def start_server(self):
        try:
            await websockets.serve(self.handle_connection, self.ip, self.port)
            self.log(f"Listening for connections on {self.host_name} ({self.ip}:{self.port})")
            self.state = State.READY
            self.pipe.send(self.state == State.READY)
        except Exception as e:
            self.log(f"[ERROR] Could not start websocket server: {e}")

    async def handle_connection(self, connection):
        self.connection = connection
        self.state = State.CONNECTED
        self.log(f"Connection established with {self.connection.remote_address[0]}:{self.connection.remote_address[1]}")

        while self.state == State.CONNECTED:
            try:
                await self.handle_message()
            except websockets.exceptions.ConnectionClosed:
                self.log(f"Connection with {self.connection.remote_address[0]}:{self.connection.remote_address[1]} dropped")
                self.connection = None
                self.state = State.READY
                break
            except Exception as e:
                self.log(f"[ERROR] Connection handler failed: {e}")

    async def handle_message(self):
        message = await self.connection.recv()
        self.last_command_received = datetime.now().strftime("%d-%m-%Y %H:%M:%S GMT")
        self.log(f"({self.last_command_received}) CubeSat received: {message}")
        await self.send_message(message)
        await self.process_command(message)

    async def send_message(self, message):
        self.log(f"Sending \"{message}\" to Ground...")

        try:
            await self.connection.send(json.dumps({"type": MessageType.MESSAGE.name.lower(), "data": message}))
            self.log(f"Sent \"{message}\" to Ground")
        except Exception as err:
            self.log(f"[ERROR] Failed to send \"{message}\": {err}")

    async def process_command(self, msg):
        self.log("Processing command...")
        tokens = msg.split(" ")
        command = tokens[0]
        self.log(f"Command: {command}")
        arguments = tokens[1:]
        self.log(f"Arguments: {arguments}")

        match command:
            case "start_phase":
                phase = int(arguments[0])
                
                match phase:
                    case 1:
                        await self.send_message("Starting phase 1...")
                    case _:
                        await self.send_message(f"{phase} is not a valid phase!")
            case "shutdown":
                await self.send_message("Shutting down...")
            case _:
                self.log(f"[ERROR] Invalid command: {command}")
                await self.send_message(f"{command} is not a valid command!")

    async def send_file(self, file_path):
        retries = 0
        
        while retries < self.MAX_RETRIES:
            self.log(f"Sending file {file_path} to Ground... (Attempt {retries + 1})")

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
                self.log("Sending file metadata...")
                await self.connection.send(json.dumps({"type": MessageType.FILEMETADATA.name.lower(), "data": {"size": file_size_in_bytes, "name": file_base_name}}))
                self.log("Sent file metadata")

                with open(file_path, "rb") as f:
                    self.log("Sending file data...")

                    while chunk := f.read(self.BUFFER_SIZE):
                        await self.connection.send(json.dumps({"type": MessageType.FILEDATA.name.lower(), "data": chunk}))

                    self.log("Sent file data")

                break
                
            except OSError as err:
                # Handle operating system error
                self.log(f"[ERROR] OS error: {err}, retrying...")
            except ConnectionError as err:
                # Handle connection-related error
                self.log(f"[ERROR] Connection error: {err}, retrying...")
            except TimeoutError as err:
                # Handle timeout-related error
                self.log(f"[ERROR] Timeout error: {err}, retrying...")
            except Exception as err:
                # Handle other general errors
                self.log(f"[ERROR] {err}, retrying...")

            retries += 1

        if retries >= self.MAX_RETRIES:
            self.log(f"[ERROR] Failed to send file {file_path} after {self.MAX_RETRIES} retries!")
    
    def get_state(self):
        return self.state
    
    def get_connection(self):
        return self.connection

    def health_check(self):
        self.log("Performing subsystem health check...")
        health_check = {}
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
            
            health_check[metric] = item_str

        health_check["Last Command Received"] = self.last_command_received
        self.log(f"Subsystem health check: {health_check}")

        return health_check