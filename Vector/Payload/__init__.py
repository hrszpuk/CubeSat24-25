from Payload.payload_controller import PayloadController


def start(pipe, log_queue):
    log_queue.put(("Payload", "Starting Subsystem"))
    payload_controller = PayloadController(log_queue)

    running = True
    while running:
        line, args = pipe.recv()
        if line == "health_check":
            variable = payload_controller.health_check()
            pipe.send(variable)
        elif line == "is_ready":
            variable = payload_controller.get_state() == "READY"
            pipe.send(variable)
        elif line == "get_state":
            variable = payload_controller.get_state()
            pipe.send(variable)
        elif line == "take_picture":
            variable = True
            payload_controller.take_picture_phase_2(args["current_yaw"])
            pipe.send(variable)
        elif line == "get_numbers":
            variable = payload_controller.identify_numbers_from_files()
            pipe.send(variable)
        elif line == "take_distance":
            variable = payload_controller.take_distance()
            pipe.send(variable)
        elif line == "detect_apriltag":
            variable = payload_controller.detect_apriltag()
            pipe.send(variable)
        elif line == "stop":
            running = False
