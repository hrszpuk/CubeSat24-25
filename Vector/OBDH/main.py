from enum import Enum
from OBDH.process_manager import ProcessManager, Logger
from OBDH.health_check import run_health_checks

Mode = Enum("Mode", [("TEST", 0), ("MANUAL", 1), ("AUTO", 2)])
State = Enum("State", [("INITIALIZING", 0), ("IDLE", 1), ("BUSY", 2)])

class OBDH:
    def __init__(self):
        self.State = State.INITIALIZING
        self.logger = Logger(log_to_console=True).get_logger()
        self.manager = ProcessManager(self.logger)
        self.mode = None
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
    
    def start_phase(self, phase):
        match phase:
            case '1':
                run_health_checks()
            case '2':
                self.logger.info("Starting Phase 2")
    
                # NOTE(Tomas): we should send numbers for confirmation and do fine tuning when facing the object but short for now
                
                # 1- Start ADCS rotation
                self.manager.send("ADCS", "phase2_rotate")
                self.logger.info("ADCS rotation started")

                # 2- Wait for instruction from ADCS to take picture
                rotating = True

                while rotating:
                    adcs_response = self.manager.receive("ADCS")
                    cmd = adcs_response["command"]
                    args = adcs_response["arguments"]

                    if cmd == "take_picture":
                        self.logger.info("ADCS instructed to take picture")
                        self.manager.send("Payload", "take_picture", args={"current_yaw": args["current_yaw"]})
                        is_picture_taken = self.manager.receive("Payload")["response"]
                        self.logger.info(f"Payload: Picture taken: {is_picture_taken}")
                    elif cmd == "rotation_complete":
                        self.logger.info("ADCS rotation complete, proceeding to image processing")
                        rotating = False

                # 3- Process images
                self.manager.send("Payload", "get_numbers")
                numbers = self.manager.receive(name="Payload")["response"]
                self.logger.info(f"Payload numbers: {numbers}")

                # 4- send the numbers to TT&C
                # 5- wait for sequence number from TT&C

                # 6- send the sequence number to ADCS
                example_sequence = [14, 15, 16]  # Example sequence numbers
                self.manager.send("ADCS", "phase2_sequence", example_sequence)