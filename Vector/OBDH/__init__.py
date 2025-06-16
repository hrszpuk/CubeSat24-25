from process_manager import ProcessManager, Logger


def start(manual=False):
    logger = Logger(log_to_console=True).get_logger()
    manager = ProcessManager(logger)

    manager.start("ADCS")
    manager.start("Payload")

    # NOTE(remy): each subsystem needs to be asked if they are 'ready' before asking it to do stuff.
    # Otherwise, stuff is still starting up while OBDH is asking it for health report data.

    if not manual:
        print("\n--- Vector CubeSat Health Check Report ---")

        manager.send("ADCS", "health_check")
        response = manager.receive("ADCS")
        print("\n--- ADCS Subsystem ---")
        for line in response[:-1]:
            print(line)
        manager.send("ADCS", "stop")

        manager.send("Payload", "health_check")
        response = manager.receive("Payload")
        print("\n--- Payload Subsystem ---")
        for line in response[:-1]:
            print(line)
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
                print("ADCS:", manager.receive("ADCS"))
                manager.send("ADCS", "stop")

                manager.send("Payload", "health_check")
                print("Payload:", manager.receive("Payload"))
                manager.send("Payload", "stop")

    manager.shutdown()
