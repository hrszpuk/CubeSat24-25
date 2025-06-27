import os
from enum import Enum
from OBDH.process_manager import ProcessManager, Logger
from OBDH.health_check import run_health_checks
from OBDH.phases import run_phase2, run_phase3a, run_phase3b, run_phase3c

State = Enum("State", [("INITIALIZING", 0), ("IDLE", 1), ("BUSY", 2)])

class OBDH:
    def __init__(self):
        self.State = State.INITIALIZING
        self.logger = Logger(log_to_console=True).get_logger()
        self.manager = ProcessManager(self.logger)
        self.phase = None
        self.subsystems = ["TTC", "ADCS", "Payload"]

        for name in self.subsystems:
            is_ready = False
            self.manager.start(name)

            while not is_ready:
                if name != "TTC":
                    self.manager.send(name, "is_ready")

                is_ready = self.manager.receive(name)["response"]

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
                case "shutdown":
                    self.manager.shutdown()
    
    def start_phase(self, phase, sequence):
        match phase:
            case '1':
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
                run_phase2(self.manager, logger=self.logger, sequence=sequence)
            case '3a':
                run_phase3a(self.manager, logger=self.logger)
            case '3b':
                run_phase3b(self.manager, logger=self.logger)
            case '3c':
                run_phase3c(self.manager, logger=self.logger)