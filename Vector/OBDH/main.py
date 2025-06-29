import os
import threading
import time
from enums import OBDHState, Phase, SubPhase
from OBDH.process_manager import ProcessManager
from OBDH.logger import Logger
from OBDH.health_check import construct_file
from OBDH.phases import run_phase2, run_phase3a, run_phase3b, run_phase3c

class OBDH:
    def __init__(self):
        self.state = OBDHState.INITIALISING
        self._logger = Logger()
        self.logger = self._logger.get_logger()
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

        self._logger.set_ttc_handler(self.manager.pipes["TTC"])
        self.state = OBDHState.READY
        self.logger.info("All subsystems are ready")

    def start_mission(self):
        print("Automatic mode")
    
    def handle_input(self):
        while True:
            if self.state == OBDHState.READY:
                input = self.manager.receive("TTC")
                self.logger.info(f"OBDH received: {input}")
                cmd = input["command"]
                args = input["arguments"]
                self.logger.info(f"Matching command: {cmd}")

                match cmd:
                    # general commands
                    case "start_phase":
                        phase = args[0]
                        self.start_phase(phase, args[1:])
                    case "test_wheel":
                        self.manager.send("ADCS", "test_wheel")
                    case "shutdown":
                        self.manager.shutdown()
                        self.logger.info(len(self.manager.processes))

                    # payload manual commands
                    case "payload_health_check":
                        self.manager.send("Payload", "health_check")
                        result = self.manager.receive("Payload")
                        self.logger.info(f"Payload health check result: {result}")
                    case "payload_take_picture":
                        path = "images/manual/"
                        self.manager.send("Payload", "take_picture_raw", args={"dir": path, "name": "manual"})
                        if os.path.exists(path+"manual_left.jpg") and os.path.exists(path+"manual_right.jpg"):
                            self.logger.info("(payload_take_photo) files were generated -> sending over TTC")
                            self.manager.send("TTC", "send_file", args={"path": path+"manual_left.jpg.jpg"})
                            self.manager.send("TTC", "send_file", args={"path": path+"manual_right.jpg"})
                        else:
                            self.logger.error("(payload_take_picture) jpg files do not exist, did stereo camera fail or images fail to save? Maybe try running a health check on the payload.")
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
                    case _:
                        self.logger.error(f"{cmd} couldn't be matched! It is likely invalid.")

    def start_phase(self, phase, args):
        match phase:
            case 1:
                self.state = OBDHState.BUSY
                self.phase = Phase.FIRST
                self.start_time = time.time()

                self.manager.send("TTC", "health_check")
                ttc_health_check = self.manager.receive("TTC")["response"]
                self.manager.send("ADCS", "health_check")
                adcs_health_check = self.manager.receive("ADCS")["response"]
                self.manager.send("Payload", "health_check")
                payload_health_check = self.manager.receive("Payload")["response"]
                self.manager.send("ADCS", "eps_health_check")
                power_health_check = self.manager.receive("ADCS")["response"]

                hc = construct_file(ttc_health_check, adcs_health_check, payload_health_check, power_health_check)

                if not hc:
                    self.logger.error("Health check failed, health.txt not generated.")
                if os.path.exists("health.txt") and hc:
                    try:
                        self.manager.send("TTC", "send_file", {"path": "health.txt"})
                        self.logger.info("Health check report sent")
                    except Exception as e:
                        self.logger.warning(f"Health check report failed: {e}")
                else:
                    self.logger.error("health.txt not found.")
                self.reset_state()

            case 2:
                self.state = OBDHState.BUSY
                self.phase = Phase.SECOND
                self.start_time = time.time()
                sequence = args["sequence"]
                run_phase2(self, self.manager, logger=self.logger, sequence=sequence)
                self.reset_state()
            case 3:
                self.state = OBDHState.BUSY
                self.phase = Phase.THIRD
                self.start_time = time.time()
                subphase = args["subphase"]

                match subphase:
                    case 'a':
                        timer = threading.Timer(300, self.reset_state)
                        self.subphase = SubPhase.a
                        distance_data, distance_data_backup = run_phase3a(self, self.manager, logger=self.logger)

                        self.manager.send("ADCS", "phase3a_complete")
                        adcs_rcv = self.manager.receive("ADCS")
                        if adcs_rcv["command"] != "readings_phase3a":
                            args = adcs_rcv["arguments"]

                        # Send data to TTC
                        self.manager.send("TTC", "send_data", {
                            "current_wheel_velocity": args["current_wheel_velocity"] + " RPM" if "current_wheel_velocity" in args else None,
                            "current_satellite_velocity": args["current_satellite_velocity"] + " º/s" if "current_satellite_velocity" in args else None,
                            "distance_data": distance_data,
                            "distance_data_backup": distance_data_backup
                        })

                        self.reset_timer(timer)
                        self.reset_state()

                    case 'b':
                        timer = threading.Timer(300, self.reset_state)
                        self.subphase = SubPhase.b
                        run_phase3b(self, self.manager, logger=self.logger)

                        self.reset_timer(timer)
                        self.reset_state()
                    case 'c':
                        timer = threading.Timer(300, self.reset_state)
                        self.subphase = SubPhase.c
                        run_phase3c(self, self.manager, logger=self.logger)
                        self.reset_timer(timer)
                        self.reset_state()
                    case _:
                        self.logger.error("Invalid subphase")        
            case _:
                self.logger.error("Invalid phase")

    def reset_state(self, timer=None):
        # Reset the state to IDLE
        if self.state != OBDHState.IDLE:
            self.state = OBDHState.IDLE
            self.phase = None
            self.subphase = None
            self.start_time = None
            self.start_time = None

    def reset_timer(self, timer):
        if timer is not None and self.state == OBDHState.BUSY:
            timer.cancel()