import multiprocessing as mp
import Vector.ADCS as adcs

from typing import Tuple

ADCS_PROCESS = 0
TTC_PROCESS = 1

class ProcessManager():
    def __init__(self):
        self.process = [self.create_tuple(adcs.start)]

    @staticmethod
    def create_tuple(start_function) -> Tuple:
        masterPipe, childPipe = mp.Pipe()
        process = mp.Process(target=start_function, args=(childPipe,))
        return (process, masterPipe, childPipe)

    def start_all(self):
        for process in self.process:
          process[0].start()

    def join_all(self):
        for process in self.process:
            process[1].send("stop")
            process[0].join()
            process[1].close()

    def send(self, id, message):
        if 0 <= id < len(self.process):
            self.process[id][1].send(message)
        else:
            raise IndexError(f"No process with ID {id}")

    def recv(self, id=ADCS_PROCESS):
        if 0 <= id < len(self.process):
            return self.process[id][1].recv()
        else:
            raise IndexError(f"No process with ID {id}")
