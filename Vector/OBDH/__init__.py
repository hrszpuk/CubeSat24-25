import os
from OBDH.process_manager import ProcessManager, Logger
from OBDH.health_check import run_health_checks
from OBDH.telemetry import Telemetry

def start_phase2(manager, logger):
    logger.info("Starting Phase 2")
    
    # NOTE(Tomas): we should send numbers for confirmation and do fine tuning when facing the object but short for now
    
    # 1- Start ADCS rotation
    manager.send("ADCS", "phase2_rotate")
    logger.info("ADCS rotation started")

    # 2- Wait for instruction from ADCS to take picture
    rotating = True

    while rotating:
        adcs_response = manager.receive("ADCS")
        cmd = adcs_response["command"]
        args = adcs_response["arguments"]

        if cmd == "take_picture":
            logger.info("ADCS instructed to take picture")
            manager.send("Payload", "take_picture", args={"current_yaw": args["current_yaw"]})
            is_picture_taken = manager.receive("Payload")["response"]
            logger.info(f"Payload: Picture taken: {is_picture_taken}")
        elif cmd == "rotation_complete":
            logger.info("ADCS rotation complete, proceeding to image processing")
            rotating = False

    # 3- Process images
    manager.send("Payload", "get_numbers")
    numbers = manager.receive(name="Payload")["response"]
    logger.info(f"Payload numbers: {numbers}")

    # 4- send the numbers to TT&C
    # 5- wait for sequence number from TT&C

    # 6- send the sequence number to ADCS
    example_sequence = [14, 15, 16]  # Example sequence numbers
    manager.send("ADCS", "phase2_sequence", example_sequence)

def start(manual=False):
    logger = Logger(log_to_console=True).get_logger()
    manager = ProcessManager(logger)

    # NOTE(remy): each subsystem needs to be asked if they are 'ready' before asking it to do stuff.
    # Otherwise, stuff is still starting up while OBDH is asking it for health report data.

    subsystems = ["TTC", "ADCS", "Payload"]  # obviously add the rest once there ready

    for name in subsystems:
        manager.start(name)
        is_ready = False

        while not is_ready:
            is_ready = manager.receive(name)["response"]

    logger.info("All subsystems are ready")
    
    if not manual:

        run_health_checks(manager)

        start_phase2(manager, logger)

        if os.path.exists("health.txt"):
            try:
                ttc.start()
                ttc.connect()

                telemetry = Telemetry(manager, ttc, interval=5)
                telemetry.start()

                ttc.send_file("health.txt", 4, 1024, "utf-8")
                logger.info("Health check report sent")
            except Exception as e:
                logger.warning(f"Health check report failed: {e}")
        else:
            logger.error("health.txt not found.")

        manager.send("ADCS", "stop")
        manager.send("Payload", "stop")

    else:
        # NOTE(remy): we might want to refactor OBDH to have a state machine for MANUAL, TEST, and PROD modes
        # MANUAL = Running manual commands (useful for debugging and testing individual parts)
        # TEST = Run test code (like the health check written above)
        # PROD = Accept commands from TT&C (like we would during the competition)
        # With this ^ we could make the code more organised and better than just a big if-else like it is now
        # This is just an idea, I think it would clean up the code a lot, up to you.
        running = True

        while running:
            userInput = input("-> ").strip().lower()

            if userInput == "stop":
                running = False
            elif userInput == "health_check":
                manager.send("ADCS", "health_check")
                response = manager.receive("ADCS")
                cmd = response["command"]
                args = response["arguments"]
                print("ADCS:", cmd, " - args:", args)
                manager.send("ADCS", "stop")

                manager.send("Payload", "health_check")
                response = manager.receive("Payload")
                cmd = response["command"]
                args = response["arguments"]
                print("Payload:", cmd, " - args:", args)
                manager.send("Payload", "stop")
            elif userInput == "phase 2":
                start_phase2(manager, logger)

    manager.shutdown()