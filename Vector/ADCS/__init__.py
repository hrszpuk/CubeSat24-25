from ADCS.adcs_controller import AdcsController

import time, random

def start(pipe, log_queue):
    log = lambda msg: log_queue.put(("ADCS", msg))
    log("Starting Subsystem")
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
                time.sleep(random.uniform(*interval_range))  # TODO: REPLACE THIS WITH SENSOR-DATA LATER
                pipe.send("take_photo")
            pipe.send("done")
        elif "photo" in line:
            path = line.split(":")[1]
            log("Received path: {}".format(path))
        elif line == "stop":
            running = False
