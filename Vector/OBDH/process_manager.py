import multiprocessing as mp
from OBDH.logger import Logger
import importlib

class ProcessManager:
    def __init__(self, logger):
        self.logger = logger
        self.processes = {}
        self.pipes = {}
        self.log_queue = mp.Queue()
        self.log_listener = mp.Process(target=self.log_listener_process, args=(self.log_queue,))
        self.log_listener.start()

    def log_listener_process(self, log_queue):
        logger = Logger(log_to_console=True).get_logger()
        while True:
            name, msg = log_queue.get()
            if msg == "STOP_LOG":
                break
            logger.info(f"[{name}] {msg}")

    def _run_subsystem(self, module_name, pipe, log_queue):
        try:
            subsystem = importlib.import_module(module_name)
            subsystem.start(pipe, log_queue)
        except Exception as e:
            log_queue.put((module_name.upper(), f"Error starting subsystem: {e}"))

    def start(self, name):
        module_name = name

        if name in self.processes:
            self.logger.warning(f"{name} already running.")
            return
        
        parent_conn, child_conn = mp.Pipe()
        proc = mp.Process(target=self._run_subsystem, args=(module_name, child_conn, self.log_queue), name=name)

        try:
            proc.start()
            self.processes[name] = proc
            self.pipes[name] = parent_conn
            self.logger.info(f"Started {name} subsystem.")
        except Exception as e:
            self.logger.error((module_name.upper(), f"Error starting subsystem: {e}"))

    def stop(self, name):
        if name not in self.processes:
            self.logger.warning(f"{name} is not running.")
            return
        try:
            print("TEST", name)
            self.pipes[name].send(("stop", {}))
        except (BrokenPipeError, EOFError, OSError) as e:
            self.logger.warning(f"Could not send stop to {name}: {e}")
        self.processes[name].join()
        self.logger.info(f"Stopped {name} subsystem.")
        del self.processes[name]
        del self.pipes[name]

    def send(self, name, msg, args={}, log=True):
        if name not in self.pipes:
            self.logger.warning(f"{name} is not running.")
            return
        
        self.pipes[name].send((msg, args))

        if log:
            if args:
                self.logger.info(f"Sent message to {name}: {msg} with args {args}")
            else:
                self.logger.info(f"Sent message to {name}: {msg}")

    def receive(self, name, timeout=None):
        conn = self.pipes[name]

        try:
            if timeout:
                if conn.poll(timeout):
                    result = conn.recv()

                    if isinstance(result, tuple) and len(result) == 2:
                        msg, args = result
                        return {"response": result, "command": msg, "arguments": args}
                    else:
                        return {"response": result}
                else:
                    self.logger.warning(f"Timeout waiting for response from {name}.")
                    return {"response": "Timed out waiting for response."}
            else:
                result = conn.recv()
                
                if isinstance(result, tuple) and len(result) == 2:
                    msg, args = result
                    return {"response": result, "command": msg, "arguments": args}
                else:
                    return {"response": result}
        except (EOFError, OSError) as e:
            self.logger.error(f"Error receiving from {name}: {e}")
            return {"response": "Error receiving"}
        
    def poll(self, name):
        conn = self.pipes[name]

        if conn.poll():
            response = conn.recv()
            cmd, args = response

            return {"response": response, "command": cmd, "arguments": args}

    def shutdown(self):
        self.logger.info("Shutting down ProcessManager...")
        for name in list(self.processes.keys()):
            self.stop(name)

        self.log_queue.put(("ProcessManager", "STOP_LOG"))
        self.log_listener.join()
        self.logger.info("Shutdown complete.")