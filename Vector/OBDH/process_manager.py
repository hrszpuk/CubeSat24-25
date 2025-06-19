import multiprocessing as mp
from OBDH.logger import Logger
import importlib
import datetime


class ProcessManager:
    def __init__(self, logger):
        self.logger = logger
        self.processes = {}
        self.pipes = {}
        self.log_queue = mp.Queue()
        self.log_listener = mp.Process(target=self.log_listener_process, args=(self.log_queue,))
        self.log_listener.start()
        self.last_command_time = None

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
        proc.start()
        self.processes[name] = proc
        self.pipes[name] = parent_conn
        self.logger.info(f"Started {name} subsystem.")

    def stop(self, name):
        if name not in self.processes:
            self.logger.warning(f"{name} is not running.")
            return
        try:
            self.pipes[name].send("stop")
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
        self.last_command_time = datetime.datetime.utcnow()
        if log:
            if args:
                self.logger.info(f"Sent message to {name}: {msg} with args {args}")
            else:
                self.logger.info(f"Sent message to {name}: {msg}")


    def receive(self, name, timeout=None):
        if name not in self.pipes:
            self.logger.warning(f"{name} is not running.")
            return None
        conn = self.pipes[name]
        try:
            if timeout:
                if conn.poll(timeout):
                    result = conn.recv()
                    if isinstance(result, tuple) and len(result) == 2:
                        msg, args = result
                        return msg, args
                    else:
                        return result, {}
                else:
                    self.logger.warning(f"Timeout waiting for response from {name}.")
                    return None, {}
            else:
                result = conn.recv()
                if isinstance(result, tuple) and len(result) == 2:
                    msg, args = result
                    return msg, args
                else:
                    return result, {}
        except (EOFError, OSError) as e:
            self.logger.error(f"Error receiving from {name}: {e}")
            return None, {}

    def shutdown(self):
        for name in list(self.processes.keys()):
            self.stop(name)
        self.log_queue.put(("ProcessManager", "STOP_LOG"))
        self.log_listener.join()
        self.logger.info("Shutdown complete.")

    def get_last_command_time(self):
        if self.last_command_time:
            return self.last_command_time.strftime("%d-%m-%Y %H:%M:%S GMT")
        return "No command sent"