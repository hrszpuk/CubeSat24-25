from ADCS.adcs_controller import AdcsController

import time, random

def start(pipe, log_queue):
    log_queue.put(("ADCS", "Starting Subsystem"))
    adcs_controller = AdcsController(log_queue)
    
    running = True
    while running:
        line = pipe.recv()
        if line == "health_check":
            variable = adcs_controller.health_check()
            pipe.send(variable)
        elif line == "is_ready":
            variable = adcs_controller.get_state() == "READY"
            pipe.send(variable)
        elif line == "phase2_rotate":
            start_time = time.time()
            duration = 10
            interval_range = (1, 2)
            while time.time() - start_time < duration:
                time.sleep(random.uniform(*interval_range))
                pipe.send("ping")
            pipe.send("done")
        elif line == "stop":
            running = False
