from Vector.Payload.payload_controller import PayloadController


def start(pipe):
    payload_controller = PayloadController()

    running = True
    while running:
        line = pipe.recv()
        if line == "health_check":
            variable = payload_controller.health_check()
            pipe.send(variable)
        elif line == "stop":
            running = False


def stop():
    pass