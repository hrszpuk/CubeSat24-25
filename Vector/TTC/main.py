import os
import threading
import asyncio
import socket
import websockets
import json
import base64
from enums import TTCState, MessageType
from datetime import datetime
from TTC.utils import get_connection_info

class TTC:
    def __init__(self, pipe, event_loop, log_queue, port=8000, buffer_size=1024, format="utf-8", byteorder_length=8, max_retries=3):
        log_queue.put(("TT&C", "Initialising..."))
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 0))

        # module configuration
        self.state = TTCState.INITIALISING
        self.pipe = pipe
        self.event_loop = event_loop
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

        log_queue.put(("TT&C", "Initialised"))

    def log(self, msg):
        self.log_queue.put(("TT&C", msg))

    def start_obdh_listener(self):
        self.log("Starting OBDH listener...")
        t = threading.Thread(target=self.handle_instructions, name="OBDH Listener", daemon=True)
        t.start()

    def handle_instructions(self):
        while True:
            if self.pipe.poll():
                instruction = self.pipe.recv()
                command = instruction[0]
                args = instruction[1] if len(instruction) == 2 else None
                self.log(f"Received instruction: {command} with args: {args}")

                match command:
                    case "get_state":
                        self.pipe.send(self.get_state())
                    case "log":
                        asyncio.run_coroutine_threadsafe(self.send_log(args["message"]), self.event_loop)
                    case "send_message":
                        asyncio.run_coroutine_threadsafe(self.send_message(args["message"]), self.event_loop)
                    case "send_data":
                        asyncio.run_coroutine_threadsafe(self.send_message(args["data"]), self.event_loop)
                    case "send_file":
                        asyncio.run_coroutine_threadsafe(self.send_file(args["path"]), self.event_loop)
                    case "health_check":
                        health = self.health_check()
                        self.pipe.send(health)
                    case "stop":
                        self.log("OBDH listener shutting down...")
                        self.event_loop.call_soon_threadsafe(self.event_loop.stop)
                        break
                    case _:
                        self.log(f"Invalid instruction received from OBDH: {command}")

    async def start_server(self):
        try:
            await websockets.serve(self.handle_connection, self.ip, self.port)
            self.log(f"Listening for connections on {self.host_name} ({self.ip}:{self.port})")
            self.state = TTCState.READY
            self.pipe.send(self.state == TTCState.READY)
            self.log("Ready")
        except Exception as e:
            self.log(f"[ERROR] Could not start WebSocket server: {e}")

    async def handle_connection(self, connection):
        self.connection = connection
        self.state = TTCState.CONNECTED
        self.last_command_received = datetime.now().strftime("%d-%m-%Y %H:%M:%S GMT")
        self.log(f"Connection established with {self.connection.remote_address[0]}:{self.connection.remote_address[1]}")

        while self.state == TTCState.CONNECTED:
            try:
                await self.handle_message()
            except websockets.exceptions.ConnectionClosed:
                self.log(f"Connection with {self.connection.remote_address[0]}:{self.connection.remote_address[1]} dropped")
                self.connection = None
                self.state = TTCState.READY
                break
            except Exception as e:
                self.log(f"[ERROR] WebSocket connection handler failed: {e}")

    async def handle_message(self):
        message = await self.connection.recv()
        self.last_command_received = datetime.now().strftime("%d-%m-%Y %H:%M:%S GMT")
        self.log(f"({self.last_command_received}) TT&C received: {message}")
        await self.process_command(message)

    async def pong(self):
        try:
            await self.connection.send("pong")
        except Exception as err:
            self.log(f"[ERROR] Failed to send \"pong\": {err}")

    async def send_log(self, message):
        self.log(f"Sending \"{message}\" to Ground...")

        try:
            await self.connection.send(json.dumps({"type": MessageType.LOG.name.lower(), "data": message}))
            self.log(f"Sent \"{message}\" to Ground")
        except Exception as err:
            self.log(f"[ERROR] Failed to send \"{message}\": {err}")

    async def send_data(self, data):
        self.log(f"Sending {data} to Ground...")

        try:
            await self.connection.send(json.dumps({"type": MessageType.DATA.name.lower(), "data": data}))
            self.log(f"Sent {data} to Ground")
        except Exception as err:
            self.log(f"[ERROR] Failed to send {data}: {err}")
    
    async def send_message(self, message):
        self.log(f"Sending \"{message}\" to Ground...")

        try:
            await self.connection.send(json.dumps({"timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S GMT"), "type": MessageType.MESSAGE.name.lower(), "data": message}))
            self.log(f"Sent \"{message}\" to Ground")
        except Exception as err:
            self.log(f"[ERROR] Failed to send \"{message}\": {err}")

    async def process_command(self, msg):
        self.log("Processing command...")
        tokens = msg.split(" ")
        command = tokens[0]
        arguments = tokens[1:] if len(tokens) > 1 else None
        self.log(f"Command: {command}")
        self.log(f"Arguments: {arguments}")

        match command:
            case "ping":
                await self.send_message("pong")
                pass
            case "get_file":
                if arguments:
                    path = arguments[0]
                    await self.send_file(path)
                else:
                    await self.send_message("No file path provided!")
            case "test_wheel":
                kp = arguments[0]
                ki = arguments[1]
                kd = arguments[2]
                #time = arguments[3]
                self.pipe.send(("test_wheel", [kp, ki, kd]))
                await self.send_message("Testing wheel...")
            case "start_phase":
                if arguments:
                    phase = int(arguments[0])
                    match phase:
                        case 1:
                            self.pipe.send(("start_phase", [phase]))
                            await self.send_message(f"Starting phase {phase}...")
                        case 2:
                            sequence = arguments[1] if len(arguments) == 2 else -None
                            self.pipe.send(("start_phase", [phase, sequence]))
                            await self.send_message(f"Starting phase {phase}...")
                        case 3:
                            subphase = arguments[1] if len(arguments) == 2 else None

                            if subphase:
                                self.pipe.send(("start_phase", [phase, subphase]))
                                await self.send_message(f"Starting phase {phase} subphase {subphase}...")
                            else:
                                await self.send_message("No subphase provided!")
                        case _:
                            await self.send_message(f"{phase} is not a valid phase!")
                else:
                    await self.send_message("No phase provided!")
            case "shutdown":
                await self.send_message("Shutting down...")
                self.pipe.send("shutdown")
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
                await self.connection.send(json.dumps({"timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S GMT"), "type": MessageType.FILEMETADATA.name.lower(), "data": {"size": file_size, "name": file_base_name}}))
                self.log("Sent file metadata")

                with open(file_path, "rb") as f:
                    self.log("Sending file data...")

                    while chunk := f.read(self.BUFFER_SIZE):
                        await self.connection.send(json.dumps({"timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S GMT"), "type": MessageType.FILEDATA.name.lower(), "data": base64.b64encode(chunk).decode("ascii")}))

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
        connection_info = get_connection_info()        

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