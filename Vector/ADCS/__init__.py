from ADCS.adcs_controller import AdcsController

import time, random

def start(pipe, log_queue):
    log_queue.put(("ADCS", "Starting Subsystem"))
    adcs_controller = AdcsController(log_queue)
    
    running = True
    while running:
        line, args = pipe.recv()
        if line == "health_check":
            variable = adcs_controller.health_check()
            pipe.send(variable)
        elif line == "eps_health_check":
            variable = adcs_controller.get_eps_health_check()
            pipe.send(variable)
        elif line == "get_state":
            variable = adcs_controller.get_state()
            pipe.send(variable)
        elif line == "phase2_rotate":
            start_time = time.time()
            duration = 2
            interval_range = (1, 2)
            while time.time() - start_time < duration:
                time.sleep(random.uniform(*interval_range))
                pipe.send(("take_picture", {"current_yaw": adcs_controller.get_current_yaw()}))
            pipe.send("rotation_complete")
        elif line == "phase2_sequence":
            sequence = args.get("sequence", None)
            numbers = args.get("numbers", None)
            if sequence is None or numbers is None:
                log_queue.put(("ADCS", "Error: Sequence or numbers not provided. Phase 2 Failed."))
            degree_distances = adcs_controller.phase2_sequence_rotation(sequence, numbers)
            pipe.send(("phase2_sequence_response", degree_distances))
        elif line == "stop":
            running = False
