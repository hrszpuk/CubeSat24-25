import multiprocessing

class ProcessManager:
    def __init__(self):
        self.processes = []

    def add_process(self, name: str, target, args=()):
        proc = multiprocessing.Process(name=name, target=target, args=args)
        self.processes.append(proc)

    def start_all(self):
        for proc in self.processes:
            proc.start()

    def stop_all(self):
        for proc in self.processes:
            if proc.is_alive():
                proc.terminate()

    def join_all(self):
        for proc in self.processes:
            proc.join()