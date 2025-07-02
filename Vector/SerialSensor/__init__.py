from SerialSensor.main import SerialSensor

def start(pipe, log_queue):

    running = True

    while running:
        line, args = pipe.recv()
        if line == "stop":
            running = False
