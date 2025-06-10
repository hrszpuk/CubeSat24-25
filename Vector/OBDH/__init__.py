from process_manager import ProcessManager
from logger import get_logger

manager = ProcessManager()

def start():
    log_queue = get_logger()
    manager.add_process()
    manager.start_all()

def stop():
    manager.stop_all()
    manager.join_all()
