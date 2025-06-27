import os
import time
from Vector.enums import OBDHState, Phase, SubPhase
from OBDH.process_manager import ProcessManager, Logger
from OBDH.health_check import run_health_checks
from OBDH.phases import run_phase2, run_phase3a, run_phase3b, run_phase3c

class OBDH:
    def __init__(self):
        self.state = OBDHState.INITIALISING
        self.logger = Logger().get_logger()
        self.manager = ProcessManager(self.logger)
        self.start_time = None
        self.phase = Phase.INITIALISATION
        self.subphase = None
        self.subsystems = ["TTC", "ADCS", "Payload"]

        for name in self.subsystems:
            is_ready = False
            self.manager.start(name)

            while not is_ready:
                if name != "TTC":
                    self.manager.send(name, "is_ready")

                is_ready = self.manager.receive(name)["response"]

        self.state = OBDHState.READY
        self.logger.info("All subsystems are ready")

    def start_mission(self):
        print("Automatic mode")
    
    def handle_input(self):
        while True:
            if not self.manager.poll("TTC"):
                break

            input = self.manager.receive("TTC")
            cmd = input.command
            args = input.arguments
            self.logger.info(f"Matching command: {cmd}")

            match cmd:                
                case "start_phase":
                    phase = args[0]
                    self.start_phase(phase, args[1:])
                case "payload_health_check":
                    self.manager.send("Payload", "health_check")
                    result = self.manager.receive("Payload")
                    self.logger.info(f"Payload health check result: {result}")
                case "payload_take_photo":
                    path = "images/phase2/"
                    self.manager.send("Payload", "take_picture", args={"current_yaw": "_manual/"})
                    if os.path.exists(path+"_manual/_left.jpeg") and os.path.exists(path+"_manual/_right.jpeg"):
                        self.logger.info("(payload_take_photo) files were generated -> sending over TTC")
                        self.manager.send("TTC", "send_file", args={"path": path+"_manual_left.jpeg"})
                        self.manager.send("TTC", "send_file", args={"path": path+"_manual_right.jpeg"})
                    else:
                        self.logger.error("(payload_take_photo) jpg files do not exist, did stereo camera fail or images fail to save? Maybe try running a health check on the payload.")
                case "payload_get_state":
                    self.manager.send("Payload", "get_state")
                    result = self.manager.receive("Payload")
                    self.logger.info(f"(payload_get_state) state: {result}")
                case "payload_is_ready":
                    self.manager.send("Payload", "is_ready")
                    result = self.manager.receive("Payload")
                    self.logger.info(f"(payload_is_ready) {'READY' if result else 'NOT READY'}")
                case "payload_get_numbers":
                    self.manager.send("Payload", "get_numbers")
                    result = self.manager.receive("Payload")
                    self.logger.info("(payload_get_numbers) result: {}".format(result))
                case "payload_take_distance":
                    self.manager.send("Payload", "take_distance")
                    result = self.manager.receive("Payload")
                    self.logger.info("(payload_take_distance) result: {}".format(result))
                case "payload_detect_apriltag":
                    self.manager.send("Payload", "detect_apriltag")
                    result = self.manager.receive("Payload")
                    if result is None:
                        self.logger.error("(payload_detect_apriltag) could not detect apriltag")
                    else:
                        self.logger.info("(payload_detect_apriltag) detected apriltag: {}".format(result))
                case "payload_restart":
                    self.manager.stop("Payload")
                    self.manager.start("Payload")
                case "shutdown":
                    self.manager.shutdown()
                case _:
                    self.logger.error(f"{cmd} couldn't be matched! It is likely invalid.")
    
    def start_phase(self, phase, args):
        match phase:
            case '1':
                self.state = OBDHState.BUSY
                self.phase = Phase.FIRST
                self.start_time = time.time()
                run_health_checks()

                if os.path.exists("health.txt"):
                    try:
                        self.manager.send("TTC", "send_file", {"path": "health.txt"})
                        self.logger.info("Health check report sent")
                    except Exception as e:
                        self.logger.warning(f"Health check report failed: {e}")
                    else:
                        self.logger.error("health.txt not found.")
            case '2':
                self.state = OBDHState.BUSY
                self.phase = Phase.SECOND
                self.start_time = time.time()
                sequence = args["sequence"]
                run_phase2(self.manager, logger=self.logger, sequence=sequence)
            case '3a':
                self.state = OBDHState.BUSY
                self.phase = Phase.THIRD
                self.start_time = time.time()
                subphase = args["subphase"]

                match subphase:
                    case 'a':
                        self.subphase = SubPhase.a
                        run_phase3a(self.manager, logger=self.logger)
                    case 'b':
                        self.subphase = SubPhase.b
                        run_phase3b(self.manager, logger=self.logger)
                    case 'c':
                        self.subphase = SubPhase.c
                        run_phase3c(self.manager, logger=self.logger)
                    case _:
                        self.logger.error("Invalid subphase")        
            case _:
                self.logger.error("Invalid phase")