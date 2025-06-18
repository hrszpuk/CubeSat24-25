from OBDH.process_manager import ProcessManager, Logger
from OBDH.health_check import run_health_checks
from OBDH.telemetry import Telemetry
from TTC.main import TTC

import threading
import time
import os

#ttc = TTC()
HeartInterval = 5

def heartbeat(ttc, logger):
    while True:
        ok = ttc.get_connection() is not None
        if ok:
            logger.debug("TT&C heartbeat: OK")
        else:
            logger.warning("TT&C heartbeat: FAILED")
        time.sleep(HeartInterval)

def start(manual=False):
    logger = Logger(log_to_console=True).get_logger()

    #threading.Thread(target=heartbeat, args=(ttc, logger), daemon=True).start()

    manager = ProcessManager(logger)
    manager.start("ADCS")
    manager.start("Payload")

    # NOTE(remy): each subsystem needs to be asked if they are 'ready' before asking it to do stuff.
    # Otherwise, stuff is still starting up while OBDH is asking it for health report data.

    subsystems = ["ADCS", "Payload"]  # obviously add the rest once there ready
    for name in subsystems:
        while True:
            manager.send(name, "is_ready", log=False)
            if manager.receive(name):
                break
    
    if not manual:

        run_health_checks(manager)

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
                print("ADCS:", manager.receive("ADCS"))
                manager.send("ADCS", "stop")

                manager.send("Payload", "health_check")
                print("Payload:", manager.receive("Payload"))
                manager.send("Payload", "stop")

    manager.shutdown()