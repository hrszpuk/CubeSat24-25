[1mdiff --git a/Vector/Payload/payload_controller.py b/Vector/Payload/payload_controller.py[m
[1mindex 568b340..8f5cc0e 100644[m
[1m--- a/Vector/Payload/payload_controller.py[m
[1m+++ b/Vector/Payload/payload_controller.py[m
[36m@@ -1,7 +1,7 @@[m
 import glob[m
[31m-#from Payload.distance_sensor import DistanceSensor[m
[31m-# from Payload.stereo_camera import StereoCamera[m
[31m-# from Payload.number_identifier import identify_numbers_from_files[m
[32m+[m[32mfrom Payload.distance_sensor import DistanceSensor[m
[32m+[m[32m#from Payload.stereo_camera import StereoCamera[m
[32m+[m[32m#from Payload.number_identifier import identify_numbers_from_files[m
 #from Payload import tag_finder[m
 import os[m
 [m
[36m@@ -11,7 +11,7 @@[m [mclass PayloadController:[m
         self.state = "INITIALIZING"[m
         self.log_queue = log_queue[m
         #self.stereo_camera = StereoCamera()[m
[31m-        #self.distance_sensor = DistanceSensor()[m
[32m+[m[32m        self.distance_sensor = DistanceSensor()[m
         self.state = "READY"[m
         self.numbers_indentified = [][m
 [m
[36m@@ -22,10 +22,10 @@[m [mclass PayloadController:[m
         health_check_text = ""[m
         errors = [][m
 [m
[31m-        # get the status of the stereo camera[m
[31m-        sc_health_check_text, sc_health_check, sc_errors = self.get_stereo_camera_health_check()[m
[31m-        health_check_text += sc_health_check_text[m
[31m-        errors.extend(sc_errors)[m
[32m+[m[32m        # # get the status of the stereo camera[m
[32m+[m[32m        # sc_health_check_text, sc_health_check, sc_errors = self.get_stereo_camera_health_check()[m
[32m+[m[32m        # health_check_text += sc_health_check_text[m
[32m+[m[32m        # errors.extend(sc_errors)[m
 [m
         # get the status of the distance sensor[m
         ds_health_check_text, ds_health_check, ds_errors = self.get_distance_sensor_health_check()[m
[36m@@ -33,7 +33,7 @@[m [mclass PayloadController:[m
         errors.extend(ds_errors)[m
 [m
         # check subsystem health[m
[31m-        if sc_health_check and ds_health_check:[m
[32m+[m[32m        if ds_health_check : #and sc_health_check and:[m
             self.status = "OK"[m
             health_check_text += "STATUS: OK"[m
         else:[m
[1mdiff --git a/Vector/TTC/__init__.py b/Vector/TTC/__init__.py[m
[1mindex 31a12ad..b4e6f19 100644[m
[1m--- a/Vector/TTC/__init__.py[m
[1m+++ b/Vector/TTC/__init__.py[m
[36m@@ -20,37 +20,31 @@[m [mdef obdh_comms(ttc, obdh_pipe):[m
     running = True[m
 [m
     while running:[m
[31m-        response = obdh_pipe.recv()[m
[31m-        print("type ", type(response))[m
[31m-        command = response[0][m
[31m-        args = response[1] if len(response) > 1 else {}[m
[32m+[m[32m        instruction = obdh_pipe.recv()[m
[32m+[m[32m        command = instruction[0][m
[32m+[m[32m        args = instruction[1] if len(instruction) > 1 else {}[m
         ttc.log(f"Received command from OBDH: {command} with arguments {args}")[m
 [m
[31m-        match command:[m
[31m-            case "health_check":[m
[31m-                try:[m
[32m+[m[32m        try:[m
[32m+[m[32m            match command:[m
[32m+[m[32m                case "log":[m
[32m+[m[32m                    msg = args["message"][m
[32m+[m[32m                    ttc.send_log(msg)[m[41m                    [m
[32m+[m[32m                case "health_check":[m
                     health_check = ttc.health_check()[m
                     obdh_pipe.send(health_check)[m
[31m-                except Exception as err:[m
[31m-                    ttc.log(f"[ERROR] Failed to process command ({command}) from OBDH: {err}")[m
[31m-            case "send_message":[m
[31m-                msg = args["message"][m
[31m-                [m
[31m-                try:[m
[32m+[m[32m                case "send_message":[m
[32m+[m[32m                    msg = args["message"][m
                     ttc.send_message(msg)[m
[31m-                except Exception as err:[m
[31m-                    ttc.log(f"[ERROR] Failed to process command ({command}) from OBDH: {err}")[m
[31m-            case "send_file":[m
[31m-                path = args["path"][m
[31m-[m
[31m-                try:[m
[32m+[m[32m                case "send_file":[m
[32m+[m[32m                    path = args["path"][m
                     ttc.send_file(path)[m
[31m-                except Exception as err:[m
[31m-                    ttc.log(f"[ERROR] Failed to process command ({command}) from OBDH: {err}")[m
[31m-            case "stop":[m
[31m-                ttc.log("Stopping subprocesses and shutting down...")[m
[31m-                processes.shutdown()[m
[31m-                running = False[m
[31m-                ttc.log("Successfully shut down")[m
[31m-            case _:[m
[31m-                ttc.log(f"Invalid command received from OBDH: {command}")[m
\ No newline at end of file[m
[32m+[m[32m                case "stop":[m
[32m+[m[32m                    ttc.log("Stopping subprocesses and shutting down...")[m
[32m+[m[32m                    processes.shutdown()[m
[32m+[m[32m                    running = False[m
[32m+[m[32m                    ttc.log("Successfully shut down")[m
[32m+[m[32m                case _:[m
[32m+[m[32m                    ttc.log(f"Invalid command received from OBDH: {command}")[m
[32m+[m[32m        except Exception as err:[m
[32m+[m[32m            ttc.log(f"[ERROR] Failed to process command ({command}) from OBDH: {err}")[m
\ No newline at end of file[m
[1mdiff --git a/Vector/TTC/main.py b/Vector/TTC/main.py[m
[1mindex be64577..e766796 100644[m
[1m--- a/Vector/TTC/main.py[m
[1m+++ b/Vector/TTC/main.py[m
[36m@@ -1,9 +1,8 @@[m
[31m-import asyncio[m
 import os[m
 import socket[m
 import websockets[m
 import json[m
[31m-from enums import TTCState, MessageType[m
[32m+[m[32mfrom Vector.enums import TTCState, MessageType[m
 from datetime import datetime[m
 from TTC.utils import get_connection_info[m
 [m
[36m@@ -65,8 +64,7 @@[m [mclass TTC:[m
     async def handle_message(self):[m
         message = await self.connection.recv()[m
         self.last_command_received = datetime.now().strftime("%d-%m-%Y %H:%M:%S GMT")[m
[31m-        if message != "ping":[m
[31m-            self.log(f"({self.last_command_received}) CubeSat received: {message}")[m
[32m+[m[32m        self.log(f"({self.last_command_received}) CubeSat received: {message}")[m
         await self.process_command(message)[m
 [m
     async def send_log(self, message):[m
[36m@@ -87,21 +85,31 @@[m [mclass TTC:[m
             self.log(f"[ERROR] Failed to send \"{message}\": {err}")[m
 [m
     async def process_command(self, msg):[m
[31m-    [m
[31m-        if msg == "ping":[m
[31m-            await self.connection.send(f"HEARTBEAT {datetime.now().time()}")[m
[31m-        else:[m
[31m-            self.log("Processing command...")[m
[31m-            tokens = msg.split(" ")[m
[31m-            command = tokens[0][m
[31m-            self.log(f"Command: {command}")[m
[31m-            arguments = tokens[1:][m
[31m-            self.log(f"Arguments: {arguments}")[m
[31m-            self.log(f"Received command \"{command}\" with {len(arguments)} arguments ({arguments})")[m
[31m-            loop = asyncio.get_running_loop()[m
[31m-            await loop.run_in_executor(None, self.pipe.send, {"response": msg, "command": command, "arguments": arguments})[m
[31m-[m
[31m-        # NOTE(remy): "cancel_phase" and other commands are all handled in OBDH/__init__.py :)[m
[32m+[m[32m        self.log("Processing command...")[m
[32m+[m[32m        tokens = msg.split(" ")[m
[32m+[m[32m        command = tokens[0][m
[32m+[m[32m        self.log(f"Command: {command}")[m
[32m+[m[32m        arguments = tokens[1:][m
[32m+[m[32m        self.log(f"Arguments: {arguments}")[m
[32m+[m
[32m+[m[32m        match command:[m
[32m+[m[32m            case "start_phase":[m
[32m+[m[32m                phase = int(arguments[0])[m
[32m+[m[41m                [m
[32m+[m[32m                match phase:[m
[32m+[m[32m                    case 1 | 2 | 3:[m
[32m+[m[32m                        self.pipe.send(msg)[m
[32m+[m[32m                        await self.send_message(f"Starting phase {phase}...")[m
[32m+[m[32m                    case _:[m
[32m+[m[32m                        await self.send_message(f"{phase} is not a valid phase!")[m
[32m+[m[32m            case "ping":[m
[32m+[m[32m                await self.send_message("pong")[m
[32m+[m[32m            case "shutdown":[m
[32m+[m[32m                await self.send_message("Shutting down...")[m
[32m+[m[32m                self.pipe.send("shutdown")[m
[32m+[m[32m            case _:[m
[32m+[m[32m                self.log(f"[ERROR] Invalid command received: {command}")[m
[32m+[m[32m                await self.send_message(f"{command} is not a valid command!")[m
 [m
     async def send_file(self, file_path):[m
         retries = 0[m
[1mdiff --git a/Vector/TTC/process_manager.py b/Vector/TTC/process_manager.py[m
[1mindex faec4f6..c85ca71 100644[m
[1m--- a/Vector/TTC/process_manager.py[m
[1m+++ b/Vector/TTC/process_manager.py[m
[36m@@ -10,6 +10,8 @@[m [mclass ProcessManager:[m
         self.logfn = logfn[m
 [m
     def start(self, name, fn, ttc, obdh_conn):[m
[32m+[m[32m        self.logfn(f"Starting process {name}...")[m
[32m+[m[41m        [m
         if name in self.processes:[m
             self.logfn(f"[ERROR] {name} already running.")[m
             return[m
[36m@@ -36,6 +38,7 @@[m [mclass ProcessManager:[m
 [m
     def shutdown(self):[m
         for name in list(self.processes.keys()):[m
[32m+[m[32m            self.logfn(f"Stopping process {name}...")[m
             self.stop(name)[m
 [m
         self.logfn("Shutdown successfully.")[m
\ No newline at end of file[m
[1mdiff --git a/Vector/TTC/utils.py b/Vector/TTC/utils.py[m
[1mindex a3b49d7..30e2a55 100644[m
[1m--- a/Vector/TTC/utils.py[m
[1m+++ b/Vector/TTC/utils.py[m
[36m@@ -3,7 +3,7 @@[m [mimport subprocess[m
 [m
 def get_connection_info(interface="wlan0"):[m
     try:[m
[31m-        result = subprocess.run(["iwconfig", interface], capture_output=True, text=True, check=True)[m
[32m+[m[32m        result = subprocess.run(["sudo iwconfig", interface], capture_output=True, text=True, check=True)[m
         output = result.stdout[m
         connection_info = {[m
             "Downlink Frequency": None,[m
