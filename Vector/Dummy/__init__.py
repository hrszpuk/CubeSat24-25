

def start(pipe, log_queue):
    log_queue.put(("Dummy", "Starting Subsystem"))


    running = True
    while running:
        line, args = pipe.recv()
        log_queue.put(("Dummy", f"Received command: {line} with args: {args}"))

        if line == "stop":
            log_queue.put(("Dummy", f"Stopping Subsystem"))
            running = False
        elif line == "echo":
            pipe.send("ECHO ECHO ECHO ECHO....")
        elif line == "is_ready":
            pipe.send(True)
        else:
            log_queue.put(("Dummy", f"Unknown command: {line}"))