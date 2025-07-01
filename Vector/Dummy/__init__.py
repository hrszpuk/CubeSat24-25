import threading, time


import threading
import time


class Dummy:
    def __init__(self):
        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.func, daemon=True)
        self.thread.start()
        print("Dummy started")

    def func(self):
        counter = 0
        while not self.stop_event.is_set():
            counter += 1
            print(f"[Dummy] tick {counter}")
            self.stop_event.wait(timeout=1.0)
        print("Dummy loop exit")

    def stop(self):
        print("Stopping Dummy...")
        self.stop_event.set()
        if self.thread:
            self.thread.join()
            self.thread = None
        print("Dummy stopped")


d = Dummy()
d.start()
time.sleep(3.5)
d.stop()
