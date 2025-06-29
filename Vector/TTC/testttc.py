import os
import socket
import websockets
import json
import base64
from datetime import datetime

class TestTTC:
    def __init__(self, event_loop, port=8000, buffer_size=1024, format="utf-8", byteorder_length=8, max_retries=3):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 0))

        # module configuration
        self.pipe = None
        self.event_loop = event_loop
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

    def log(self, msg):
        print(msg)

    async def start_server(self):
        try:
            await websockets.serve(self.handle_connection, self.ip, self.port)
            self.log(f"Listening for connections on {self.host_name} ({self.ip}:{self.port})")
        except Exception as e:
            self.log(f"[ERROR] Could not start WebSocket server: {e}")

    async def handle_connection(self, connection):
        self.connection = connection
        self.last_command_received = datetime.now().strftime("%d-%m-%Y %H:%M:%S GMT")
        self.log(f"Connection established with {self.connection.remote_address[0]}:{self.connection.remote_address[1]}")

        while True:
            try:
                await self.handle_message()
            except websockets.exceptions.ConnectionClosed:
                self.log(f"Connection with {self.connection.remote_address[0]}:{self.connection.remote_address[1]} dropped")
                self.connection = None
                break
            except Exception as e:
                self.log(f"[ERROR] WebSocket connection handler failed: {e}")

    async def handle_message(self):
        message = await self.connection.recv()
        self.last_command_received = datetime.now().strftime("%d-%m-%Y %H:%M:%S GMT")
        self.log(f"({self.last_command_received}) CubeSat received: {message}")
        await self.process_command(message)

    async def pong(self):
        try:
            await self.connection.send("pong")
        except Exception as err:
            self.log(f"[ERROR] Failed to send \"pong\": {err}")

    async def send_log(self, message):
        self.log(f"Sending \"{message}\" to Ground...")

        try:
            await self.connection.send(json.dumps({"timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S GMT"), "type": "log", "data": message}))
        except Exception as err:
            self.log(f"[ERROR] Failed to send \"{message}\": {err}")

    async def send_data(self, data):
        self.log(f"Sending {data} to Ground...")

        try:
            await self.connection.send(json.dumps({"type": "data", "data": data}))
            self.log(f"Sent {data} to Ground")
        except Exception as err:
            self.log(f"[ERROR] Failed to send {data}: {err}")

    async def send_message(self, message):
        self.log(f"Sending \"{message}\" to Ground...")

        try:
            await self.connection.send(json.dumps({"timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S GMT"), "type": "message", "data": message}))
            self.log(f"Sent \"{message}\" to Ground")
        except Exception as err:
            self.log(f"[ERROR] Failed to send \"{message}\": {err}")

    async def process_command(self, msg):
        self.log("Processing command...")
        tokens = msg.split(" ")
        command = tokens[0]
        arguments = tokens[1:] if len(tokens) > 1 else None
        self.log(f"Command: {command}; Arguments: {arguments}")

        match command:
            case "ping":
                await self.pong()
            case "get_file":
                if arguments:
                    path = arguments[0]
                    await self.send_message(f"Sending file {path}...")
                    await self.send_file(path)
                else:
                    await self.send_message("No file path provided!")
            case "health_check":
                await self.send_message(f"'{self.health_check()}'")
            case "start_phase":
                if arguments:
                    phase = int(arguments[0])
                    subphase = arguments[1] if len(arguments) == 2 else None
                    
                    match phase:
                        case 1 | 2:
                            self.pipe.send(msg)
                            await self.send_message(f"Starting phase {phase}...")
                        case 3:
                            if subphase:
                                self.pipe.send(msg)
                                await self.send_message(f"Starting phase {phase} subphase {subphase}...")
                            else:
                                await self.send_message("No subphase provided!")
                        case _:
                            await self.send_message(f"{phase} is not a valid phase!")
                else:
                    await self.send_message("No phase provided!")
            case "shutdown":
                await self.send_message("Shutting down...")
            case _:
                self.log(f"[ERROR] Invalid command received: {command}")
                await self.send_message(f"{command} is not a valid command!")

    async def send_file(self, file_path):
        retries = 0
        
        while retries < self.MAX_RETRIES:
            self.log(f"Sending file {file_path} to Ground... (Attempt {retries + 1})")

            try:
                if not os.path.exists(file_path):
                    self.log(f"[ERROR] {file_path} does not exist!")
                    break

                file_base_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                self.log("Sending file metadata...")
                await self.connection.send(json.dumps({"timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S GMT"), "type": "filemetadata", "data": {"size": file_size, "name": file_base_name}}))
                self.log("Sent file metadata")

                with open(file_path, "rb") as f:
                    self.log("Sending file data...")

                    while chunk := f.read(self.BUFFER_SIZE):
                        await self.connection.send(json.dumps({"timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S GMT"), "type": "filedata", "data": base64.b64encode(chunk).decode("ascii")}))

                    await self.send_message("File send complete")
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
        connection_info = connection_info = {
            "Downlink Frequency": None,
            "Uplink Frequency": None,
            "Signal Strength": None,
            "Data Transmission Rate": None
        }

        for metric, value in connection_info.items():
            if value is not None:
                item_str = f"{abs(value)}"

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