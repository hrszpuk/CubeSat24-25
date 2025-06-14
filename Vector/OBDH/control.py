from multiprocessing import Queue

from Vector.OBDH.health_check import run_health_checks
from process_manager import ProcessManager
from logger import get_logger

import time
import threading

commands_queue = Queue()
responses_queue = Queue()

logger = get_logger()
manager = ProcessManager()

def start():
    manager.add_process()  # TTC
    manager.add_process()  # ACOS
    manager.add_process()  # Payload
    manager.add_process()  # ESP
    manager.start_all()

    def health_loop():
        while True:
            report = run_health_checks() # Give all subsystems
            responses_queue.put({
                "cmd": "health_report",
                "report": report
            })
            time.sleep(5)
    threading.Thread(target=health_loop, daemon=True).start()

def stop():
    manager.stop_all()
    manager.join_all()
