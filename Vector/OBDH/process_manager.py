import subprocess
from pathlib import Path
import threading

class ProcessManager:
    def __init__(self):
        self.processes = []
        self.subprocess_output = {}
        self.output_threads = {}

    def add_process(self, name: str, target=None, args=()):
        if name == "ADCS":
            script_path = Path("ADCS/__init__.py")
            if not script_path.exists():
                raise FileNotFoundError(f"ADCS script not found at {script_path}")
            
            try:
                proc = subprocess.Popen(
                    ["python3", "-u", str(script_path)],
                    # stdout=None,  # Let output print directly
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                self.processes.append(proc)
                self.subprocess_output[name] = proc.stdout
                
                # Start a thread to print output in real-time
                def print_output():
                    while True:
                        line = proc.stdout.readline()
                        if not line and proc.poll() is not None:
                            break
                        if line:
                            print(f"[{name}] {line.strip()}")
                
                t = threading.Thread(target=print_output, daemon=True)
                t.start()
                self.output_threads[name] = t
                
            except Exception as e:
                raise RuntimeError(f"Failed to start {name} process: {str(e)}")

    def stop_all(self):
        for proc in self.processes:
            if proc.poll() is None:
                proc.terminate()  # More graceful than kill()
        for proc in self.processes:
            proc.wait()

    def join_all(self):
        for proc in self.processes:
            proc.wait()