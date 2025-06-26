import os
from enum import Enum
from OBDH.process_manager import ProcessManager, Logger
from OBDH.health_check import run_health_checks

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

                # 4- send the sequence number to ADCS

                data = []
                number_distances = []
                degree_distances = []

                waiting_for_completion = True
                self.manager.send("ADCS", "phase2_sequence", {"sequence" : sequence, "numbers" : numbers})
                while waiting_for_completion:
                    adcs_rcv = self.manager.receive(name="ADCS")

                    if adcs_rcv["command"] == "take_distance":
                        self.logger.info("ADCS instructed to take distance")
                        self.manager.send("Payload", "take_distance")
                        number_distance = self.manager.receive(name="Payload")["response"]
                        degree_distances.append(number_distance)
                    elif adcs_rcv["command"] == "SEQUENCE_ROTATION_COMPLETE":
                        payload_rcv = self.manager.receive(name="Payload")
                        self.logger.info("ADCS sequence rotation complete")
                        degree_distances = adcs_rcv["response"]

                        waiting_for_completion = False

                for i, distance in enumerate(number_distances):
                    data[sequence[i]] = {
                        "angle_degree": numbers[sequence[i] if i < len(numbers) else None],
                        "distance away in cm": distance,
                        "angle_variation": degree_distances[i] if i < len(degree_distances) else None
                    }
                self.manager.send(name="TTC", msg="send_message", message={"data": data})