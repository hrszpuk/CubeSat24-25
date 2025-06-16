from ADCS.adcs_controller import AdcsController

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
        elif line == "stop":
            running = False
