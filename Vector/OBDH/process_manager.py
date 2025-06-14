import subprocess

class ProcessManager:
    def __init__(self):
        self.processes = []
        self.subprocess_output = {}

    def add_process(self, name: str, target=None, args=()):
        if name == "ADCS":
            proc = subprocess.Popen(
                ["python3", "-u", "ADCS/__init__.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            self.processes.append(proc)
            self.subprocess_output[name] = proc.stdout

    def get_stdout(self, name):
        return self.subprocess_output.get(name)

    def stop_all(self):
        for proc in self.processes:
            if proc.poll() is None:
                proc.kill()

    def join_all(self):
        for proc in self.processes:
            proc.wait()
