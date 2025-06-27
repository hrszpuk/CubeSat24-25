import os
import threading
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
            self.logger.info(f"Received command {cmd} with arguments {args} from TT&C")

            match cmd:                
                case "start_phase":
                    phase = args[0]
                    self.start_phase(phase)
                case "cancel_phase":
                    if self.state == OBDHState.BUSY:
                        self.logger.info("Cancelling current phase")
                        self.reset_state()
                case "shutdown":
                    self.manager.shutdown()
    
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
                self.reset_state()

            case '2':
                self.state = OBDHState.BUSY
                self.phase = Phase.SECOND
                self.start_time = time.time()
                sequence = args["sequence"]
                run_phase2(self, self.manager, logger=self.logger, sequence=sequence)
                self.reset_state()
            case '3a':
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
                        self.manager.send("TTC", "send_message", {
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