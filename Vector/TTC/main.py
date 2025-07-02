import os
import threading
import asyncio
import socket
import websockets
import json
import time
from enums import TTCState, MessageType
from datetime import datetime
from TTC.utils import get_command_and_data_handling_status, get_connection_info, zip_folder, zip_file

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

    def start_obdh_listener(self):
        self.log("Starting OBDH listener...")
        t = threading.Thread(target=self.handle_instructions, name="OBDH Listener", daemon=True)
        t.start()

    def handle_instructions(self):
        while True:
            if self.pipe.poll():
                cmd, args = self.pipe.recv()
                self.log(f"Received instruction: {cmd} with arguments: {args}")

                match cmd:                    
                    case "get_state":
                        self.pipe.send(self.state)
                    case "log":
                        if args["message"]:
                            asyncio.run_coroutine_threadsafe(self.send_log(args["message"]), self.event_loop)
                        else:
                            self.log("[ERROR] No log message provided!")
                    case "send_message":
                        if args["message"]:
                            asyncio.run_coroutine_threadsafe(self.send_message(args["message"]), self.event_loop)
                        else:
                            self.log("[ERROR] No message provided!")
                    case "send_data":
                        if args["data"]:
                            asyncio.run_coroutine_threadsafe(self.send_data(args["subsystem"], args["data"]), self.event_loop)
                        else:
                            self.log("[ERROR] No message provided!")
                    case "send_file":
                        if args["path"]:
                            asyncio.run_coroutine_threadsafe(self.send_file(args["path"]), self.event_loop)
                        else:
                            self.log("[ERROR] No file path provided!")
                    case "send_folder":
                        if args["path"]:
                            asyncio.run_coroutine_threadsafe(self.send_folder(args["path"]), self.event_loop)
                        else:
                            self.log("[ERROR] No folder path provided!")
                    case "health_check":
                        health = self.health_check()
                        self.pipe.send(health)
                    case "imu_data":
                        asyncio.run_coroutine_threadsafe(self.send_message(args["imu_data"]), self.event_loop)
                    case "stop":
                        self.log("OBDH listener shutting down...")
                        self.event_loop.call_soon_threadsafe(self.event_loop.stop)
                        break
                    case _:
                        self.log(f"Invalid instruction received from OBDH: {cmd}")

    def send_command(self, input, arguments=None):
        self.pipe.send((input, arguments))

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
        self.log(f"Connection established with {self.connection.remote_address[0]}:{self.connection.remote_address[1]}")
        await self.send_status()

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
        try:
            message = await self.connection.recv()
            self.last_command_received = datetime.now().strftime("%d-%m-%Y %H:%M GMT")
            self.log(f"({self.last_command_received}) TT&C received: {message}")
            await self.send_status()
            await self.process_command(message)
        except Exception as e:
            self.log(f"[ERROR] WebScoket message handler failed: {e}")

    async def pong(self):
        try:
            await self.connection.send("pong")
        except Exception as err:
            self.log(f"[ERROR] Failed to send \"pong\": {err}")

    async def send_status(self):
        health = self.health_check()
        status = get_command_and_data_handling_status()

        for key, value in health:
            status[key] = value

        await self.send_data("TTC", status)

    async def send_log(self, message):
        if (self.state == TTCState.CONNECTED):
            self.log(f"Sending \"{message}\" to Ground...")

            try:
                await self.connection.send(json.dumps({"type": MessageType.LOG.name.lower(), "data": message}))
                self.log(f"Sent \"{message}\" to Ground")
            except Exception as err:
                self.log(f"[ERROR] Failed to send \"{message}\": {err}")
        else:
            self.log("Not connected to ground, log not sent")

    async def send_data(self, subsystem, data):
        self.log(f"Sending data from {subsystem} ({data}) to Ground...")

        try:
            await self.connection.send(json.dumps({"type": MessageType.DATA.name.lower(), "subsystem": subsystem, "data": data}))
            self.log(f"Sent data from {subsystem} ({data}) to Ground")
        except Exception as err:
            self.log(f"[ERROR] Failed to send data from {subsystem} ({data}): {err}")    
    
    async def send_message(self, message):
        self.log(f"Sending \"{message}\" to Ground...")

        try:
            await self.connection.send(json.dumps({"timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "type": MessageType.MESSAGE.name.lower(), "data": message}))
            self.log(f"Sent \"{message}\" to Ground")
        except Exception as err:
            self.log(f"[ERROR] Failed to send \"{message}\": {err}")

    async def send_error(self, message):
        self.log(f"Sending \"{message}\" to Ground...")

        try:
            await self.connection.send(json.dumps({"timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "type": MessageType.MESSAGE.name.lower(), "data": f"[ERROR] {message}"}))
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
                await self.connection.send("pong")
            case "get_file":
                if arguments:
                    path = arguments[0]

                    if os.path.exists(path):
                        if os.path.isfile(path):
                            await self.send_file(path)
                        else:
                            await self.send_error(f"{path} is not a file!")
                    else:
                        await self.send_error(f"{path} does not exist!")
                else:
                    await self.send_error("No file path provided!")
            case "get_folder":
                if arguments:
                    path = arguments[0]

                    if os.path.exists(path):
                        if os.path.isdir(path):
                            await self.send_folder(path)
                        else:
                            await self.send_error(f"{path} is not a folder!")
                    else:
                        await self.send_error(f"{path} does not exist!")
                else:
                    await self.send_error("No folder path provided!")
            case "test_wheel":
                kp = arguments[0]
                ki = arguments[1]
                kd = arguments[2]
                t = arguments[3]
                degree = arguments[4]
                self.send_command("test_wheel", [kp, ki, kd, t, degree])
                await self.send_message("Testing wheel...")
            case "stop_wheel":
                self.send_command("stop_wheel")
                await self.send_message("Stopping wheel...")
            case "calibrate_sun_sensors":
                self.send_command("calibrate_sun_sensors")
                await self.send_message("Calibrating sun sensors...")
            case "imu":
                initial_time = time.time()

                while (time.time() - initial_time) < 30:
                    self.send_command("imu")
            case "start_phase":
                if arguments:
                    phase = int(arguments[0])

                    match phase:
                        case 1:
                            self.send_command("start_phase", {"phase": phase})
                            await self.send_message(f"Starting phase {phase}...")
                        case 2:
                            if len(arguments) > 2:
                                sequence = ','.join(arguments[1:])
                            else:
                                sequence = arguments[1] if len(arguments) == 2 else None

                            if sequence:
                                sequence_list = [int(number) for number in sequence.split(",")]
                                self.send_command("start_phase", {"phase": phase, "sequence": sequence_list})
                                await self.send_message(f"Starting phase {phase}...")
                            else:
                                await self.send_error("No sequence provided!")
                        case 3:
                            subphase = arguments[1] if len(arguments) == 2 else None

                            if subphase:
                                self.send_command("start_phase", {"phase": phase, "subphase": subphase})
                                await self.send_message(f"Starting phase {phase} subphase {subphase}...")
                            else:
                                await self.send_error("No subphase provided!")
                        case _:
                            await self.send_error(f"{phase} is not a valid phase!")
                else:
                    await self.send_error("No phase provided!")
            case "payload_health_check" | "payload_take_picture" | "payload_get_state" | "payload_is_ready" | "payload_get_numbers" | "payload_take_distance" | "payload_detect_apriltag" | "payload_restart":
                self.send_command(command)
            case "shutdown":
                await self.send_message("Shutting down...")
                self.send_command("shutdown")
            case _:
                self.log(f"[ERROR] Invalid command received: {command}")
                await self.send_error(f"{command} is not a valid command!")

    async def send_file(self, path):
        retries = 0
        
        while retries < self.MAX_RETRIES:
            self.log(f"Sending file {path} to Ground... (Attempt {retries + 1})")

            try:
                zip_path = zip_file(path)
                zip_file_size = os.path.getsize(zip_path)
                self.log("Sending file metadata...")
                await self.connection.send(json.dumps({"timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "type": MessageType.FILEMETADATA.name.lower(), "data": {"size": zip_file_size, "name": f"{os.path.basename(path)}.zip"}}))
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
                self.log(f"[ERROR] {err}, retrying...")
            finally:
                if zip_path and os.path.exists(zip_path):
                    os.unlink(zip_path)

            retries += 1

        if retries >= self.MAX_RETRIES:
            self.log(f"[ERROR] Failed to send file {path} after {self.MAX_RETRIES} retries!")

    async def send_folder(self, path):
        retries = 0
        
        while retries < self.MAX_RETRIES:
            self.log(f"Sending folder {path} to Ground... (Attempt {retries + 1})")

            try:
                zip_path = zip_folder(path)
                zip_file_size = os.path.getsize(zip_path)
                self.log("Sending folder metadata...")
                await self.connection.send(json.dumps({"timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "type": MessageType.FILEMETADATA.name.lower(), "data": {"size": zip_file_size, "name": f"{os.path.basename(path)}.zip"}}))
                self.log("Sent folder metadata")

                with open(zip_path, "rb") as f:
                    self.log("Sending folder data...")
                    await self.connection.send("File transfer started")

                    while chunk := f.read(self.BUFFER_SIZE):
                        await self.connection.send(chunk)

                    self.log("Sent folder data")
                    await self.connection.send("File transfer complete")

                break
            except Exception as err:
                self.log(f"[ERROR] {err}, retrying...")
            finally:
                if zip_path and os.path.exists(zip_path):
                    os.unlink(zip_path)

            retries += 1

        if retries >= self.MAX_RETRIES:
            self.log(f"[ERROR] Failed to send folder {path} after {self.MAX_RETRIES} retries!")