import os
import socket
import websockets
import json
from datetime import datetime
from TTC.utils import get_command_and_data_handling_status, zip_file

class TestTTC:
    def __init__(self, event_loop, port=8000, buffer_size=1024, format="utf-8", byteorder_length=8, max_retries=3):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 0))

        # module configuration
        self.pipe = None
        self.event_loop = event_loop
        self.backlog = []
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
        self.log(f"Connection established with {self.connection.remote_address[0]}:{self.connection.remote_address[1]}")

        while self.connection:
            try:
                if len(self.backlog):
                    await self.process_backlog()
                
                await self.handle_message()                
            except websockets.exceptions.ConnectionClosed:
                self.log(f"Connection with {self.connection.remote_address[0]}:{self.connection.remote_address[1]} dropped")
                self.connection = None
            except Exception as e:
                self.log(f"[ERROR] WebSocket connection handler failed: {e}")

    async def handle_message(self):
        await self.send_status()
        message = await self.connection.recv()
        self.last_command_received = datetime.now().strftime("%d-%m-%Y %H:%M GMT")
        self.log(f"({self.last_command_received}) CubeSat received: {message}")
        await self.process_command(message)

    async def process_backlog(self):
        for item in self.backlog:
            for instruction, arguments in item.items():
                match instruction:
                    case "send_log":
                        await self.send_log(arguments[0])

    async def pong(self):
        try:
            await self.connection.send("pong")
        except Exception as err:
            self.log(f"[ERROR] Failed to send \"pong\": {err}")

    async def send_status(self):
        status = get_command_and_data_handling_status()
        status["Last Command Received"] = self.last_command_received
        await self.send_data("TTC", status)
    
    async def send_log(self, message):
        if self.connection:
            self.log(f"Sending \"{message}\" to Ground...")

            try:
                await self.connection.send(json.dumps({"type": "log", "data": message}))
                self.log(f"Sent \"{message}\" to Ground")
            except Exception as err:
                self.log(f"[ERROR] Failed to send \"{message}\": {err}")
        else:
            self.backlog.append({"instruction": "send_log", "arguments": [message]})
            self.log(f"Not connected to Ground, send_log instruction added to backlog with arguments: {[message]}")

    async def send_data(self, subsystem, data):
        self.log(f"Sending data from {subsystem} ({data}) to Ground...")

        try:
            await self.connection.send(json.dumps({"type": "data", "subsystem": subsystem, "data": data}))
            self.log(f"Sent data from {subsystem} ({data}) to Ground")
        except Exception as err:
            self.log(f"[ERROR] Failed to send data from {subsystem} ({data}): {err}")

    async def send_error(self, message):
        self.log(f"Sending \"{message}\" to Ground...")

        try:
            await self.connection.send(json.dumps({"timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "type": "message", "data": f"[ERROR] {message}"}))
            self.log(f"Sent \"{message}\" to Ground")
        except Exception as err:
            self.log(f"[ERROR] Failed to send \"{message}\": {err}")

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
                    await self.send_file(path)
                else:
                    await self.send_error("No file path provided!")
            case "health_check":
                await self.send_message(f"'{self.health_check()}'")
            case "start_phase":
                if arguments:
                    phase = int(arguments[0])
                    
                    match phase:
                        case 1:
                            self.pipe.send(("start_phase", {"phase": phase}))
                            await self.send_message(f"Starting phase {phase}...")
                        case 2:
                            if len(arguments) > 2:
                                sequence = ','.join(arguments[1:])
                            else:
                                sequence = arguments[1] if len(arguments) == 2 else None

                            if sequence:
                                sequence_list = [int(number) for number in sequence.split(",")]
                                await self.send_message(f"Starting phase {phase}...")
                            else:
                                await self.send_error("No sequence provided!")
                        case 3:
                            subphase = arguments[1] if len(arguments) == 2 else None

                            if subphase:
                                self.pipe.send(("start_phase", {"phase": phase, "subphase": subphase}))
                                await self.send_message(f"Starting phase {phase} subphase {subphase}...")
                            else:
                                await self.send_error("No subphase provided!")
                        case _:
                            await self.send_error(f"{phase} is not a valid phase!")
                else:
                    await self.send_error("No phase provided!")
            case "shutdown":
                await self.shutdown()
            case _:
                self.log(f"[ERROR] Invalid command received: {command}")
                await self.send_error(f"{command} is not a valid command!")

    async def send_file(self, file_path):
        retries = 0
        
        while retries < self.MAX_RETRIES:
            self.log(f"Sending file {file_path} to Ground... (Attempt {retries + 1})")

            try:
                if not os.path.exists(file_path):
                    self.log(f"[ERROR] {file_path} does not exist!")
                    break

                zip_path = zip_file(file_path)
                zip_file_size = os.path.getsize(zip_path)
                self.log("Sending file metadata...")
                await self.connection.send(json.dumps({"timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S GMT"), "type": "filemetadata", "data": {"size": zip_file_size, "name": f"{os.path.basename(file_path)}.zip"}}))
                self.log("Sent file metadata")

                with open(zip_path, "rb") as f:
                    self.log("Sending file data...")
                    await self.connection.send("File transfer started")

                    while chunk := f.read(self.BUFFER_SIZE):
                        await self.connection.send(chunk)

                    self.log("Sent file data")
                    await self.connection.send("File transfer complete")

                break
            except Exception as err:
                # Handle other general errors
                self.log(f"[ERROR] {err}, retrying...")
            finally:
                if zip_path and os.path.exists(zip_path):
                    os.unlink(zip_path)

            retries += 1

        if retries >= self.MAX_RETRIES:
            self.log(f"[ERROR] Failed to send file {file_path} after {self.MAX_RETRIES} retries!")
    
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
    
    async def shutdown(self):
        self.log("Shutting down...")

        if self.connection:
            await self.connection.close(1001, "Server shutting down")
            
        self.event_loop.stop()
        self.event_loop.close()