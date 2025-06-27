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
                    self.start_phase(phase)
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