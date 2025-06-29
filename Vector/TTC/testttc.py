import os
import threading
import asyncio
import socket
import websockets
import json
import base64
from datetime import datetime

class TestTTC:
    def __init__(self, pipe, event_loop, log_queue, port=8000, buffer_size=1024, format="utf-8", byteorder_length=8, max_retries=3):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 0))

        # module configuration
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

    def start_obdh_listener(self):
        self.log("Starting OBDH listener...")
        t = threading.Thread(target=self.handle_instructions, name="OBDH Listener", daemon=True)
        t.start()
        self.log(f"Ready")

    def handle_instructions(self):
        while True:
            if self.pipe.poll():
                instruction = self.pipe.recv()
                command = instruction[0]
                args = instruction[1] if len(instruction) == 2 else None
                self.log(f"Received command: {command} with args: {args} from OBDH")
                pipe_loop = asyncio.new_event_loop()

                match command:
                    case "stop":
                        self.log("OBDH listener shutting down...")
                        self.event_loop.call_soon_threadsafe(self.event_loop.stop)
                        break
                    case "log":
                        asyncio.run_coroutine_threadsafe(self.send_log(args["message"]), pipe_loop)
                    case "send_message":
                        asyncio.run_coroutine_threadsafe(self.send_message(args["message"]), pipe_loop)
                    case "send_file":
                        asyncio.run_coroutine_threadsafe(self.send_file(args["path"]), pipe_loop)
                    case "health_check":
                        health = self.health_check()
                        self.pipe.send(health)
                    case _:
                        self.log(f"Invalid instruction received from OBDH: {command}")

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

    async def send_log(self, message):
        self.log(f"Sending \"{message}\" to Ground...")

        try:
            await self.connection.send(json.dumps({"timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S GMT"), "type": "log", "data": message}))
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
                pass
            case "get_file":
                if arguments:
                    path = arguments[0]
                    await self.send_message(f"Sending file {path}...")
                    await self.send_file(path)
                else:
                    await self.send_message("No file path provided!")
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