import importlib
import multiprocessing as mp
from OBDH.logger import Logger

class ProcessManager:
    def __init__(self, logger):
        self.logger = logger
        self.processes = {}
        self.pipes = {}

        self.log_queue = mp.Queue()
        self.log_listener = mp.Process(target=self.log_listener_process, args=(self.log_queue,))
        self.log_listener.start()

        self.telemetry_queue = mp.Queue()
        self.telemetry_listener = mp.Process(target=self.telemetry_listener_process, args=(self.telemetry_queue,))
        self.telemetry_listener.start()

    def telemetry_listener_process(self, log_queue):
        # NOTE(remy): telemetry data bypasses the logger and just uses queue + pipes because I've stopped caring at this point
        while True:
            subsystem, origin, data, timestamp = log_queue.get()
            # NOTE(remy): origin = what it is (gyroscope, temperature, rpm, etc)
            self.pipes["TTC"].send(("send_data", {"subsystem": subsystem, "label": origin, "data": data, "timestamp": timestamp}))
            #print("data", {"subsystem": subsystem, "label": origin, "timestamp": timestamp, "data": data})

    def log_listener_process(self, log_queue):
        logger = Logger(log_to_console=True).get_logger()
        while True:
            name, msg = log_queue.get()
            if msg == "STOP_LOG":
                break
            logger.info(f"[{name}] {msg}")

    def _run_subsystem(self, module_name, pipe, log_queue, telemetry):
        try:
            subsystem = importlib.import_module(module_name)
            subsystem.start(pipe, log_queue, telemetry)
        except Exception as e:
            log_queue.put((module_name.upper(), f"Error starting subsystem: {e}"))

    def start(self, name):
        module_name = name

        if name in self.processes:
            self.logger.warning(f"{name} already running.")
            return

        parent_conn, child_conn = mp.Pipe()
        proc = mp.Process(target=self._run_subsystem, args=(module_name, child_conn, self.log_queue, self.telemetry_queue), name=name)

        try:
            proc.start()
            self.processes[name] = proc
            self.pipes[name] = parent_conn
            self.logger.info(f"Started {name} subsystem.")
        except Exception as e:
            self.logger.error((module_name.upper(), f"Error starting subsystem: {e}"))

    def send(self, name, msg, args=None, log=True):
        if name not in self.pipes:
            self.logger.warning(f"{name} is not running.")
            return

        self.pipes[name].send((msg, args))

        if log:
            self.logger.info(f"Sent instruction to {name}: {msg} with args {args}")

    def receive(self, name, timeout=None):
        conn = self.pipes[name]

        try:
            if timeout:
                if conn.poll(timeout):
                    result = conn.recv()

                    if isinstance(result, tuple) and len(result) == 2:
                        cmd, args = result
                        return {"response": result, "command": cmd, "arguments": args}
                    else:
                        return {"response": result}
                else:
                    self.logger.warning(f"Timeout waiting for response from {name}.")
                    return None
            else:
                result = conn.recv()

                if isinstance(result, tuple) and len(result) == 2:
                    cmd, args = result
                    return {"response": result, "command": cmd, "arguments": args}
                else:
                    return {"response": result}
        except (EOFError, OSError) as e:
            self.logger.error(f"Error receiving from {name}: {e}")
            return None
        
    def stop(self, name):
        if name not in self.processes:
            self.logger.warning(f"{name} is not running.")
            return
        
        try:
            self.pipes[name].send(("stop", None))
        except (BrokenPipeError, EOFError, OSError) as e:
            self.logger.warning(f"Could not send stop to {name}: {e}")
        
        self.processes[name].join()
        self.logger.info(f"Stopped {name} subsystem.")
        del self.processes[name]
        del self.pipes[name]
        
    def shutdown(self):
        self.logger.info("Shutting down ProcessManager...")

        for name in list(self.processes.keys()):
            self.stop(name)

        self.log_queue.put(("ProcessManager", "STOP_LOG"))
        self.log_listener.join()
        self.logger.info("Shutdown complete.")