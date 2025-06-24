import multiprocessing as mp

class ProcessManager:
    def __init__(self):
        self.logfn = None
        self.processes = {}
        self.pipes = {}
    
    def set_logfn(self, logfn):
        self.logfn = logfn

    def start(self, name, fn, ttc, obdh_conn):
        if name in self.processes:
            self.logfn(f"[ERROR] {name} already running.")
            return
        
        try:
            parent_conn, child_conn = mp.Pipe()
            proc = mp.Process(target=fn, args=(ttc, obdh_conn), name=name)
            proc.start()
            self.processes[name] = proc
            self.pipes[name] = parent_conn
            self.logfn(f"Started process {name}")
        except Exception as err:
            self.logfn(f"[ERROR] Failed to start process {name}: {err}")

    def stop(self, name):
        if name not in self.processes:
            self.logfn(f"[ERROR] {name} is not running.")
            return
        
        try:
            self.pipes[name].send("stop")
        except (BrokenPipeError, EOFError, OSError) as e:
            self.logfn(f"[ERROR] Could not send stop to {name}: {e}")

        self.processes[name].join()
        self.logfn(f"Stopped {name} subsystem.")
        del self.processes[name]
        del self.pipes[name]

    def shutdown(self):
        for name in list(self.processes.keys()):
            self.stop(name)

        self.logfn("Shutdown complete.")