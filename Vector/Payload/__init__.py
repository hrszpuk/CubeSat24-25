from Payload.payload_controller import PayloadController


def start(pipe, log_queue):
    log_queue.put(("Payload", "Starting Subsystem"))
    payload_controller = PayloadController()

    running = True
    while running:
        line = pipe.recv()
        if line == "health_check":
            variable = payload_controller.health_check()
            pipe.send(variable)
        elif line == "stop":
            running = False
