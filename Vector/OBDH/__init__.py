from process_manager import ProcessManager
from logger import get_logger

manager = ProcessManager()

def start():
    manager.add_process(name="ADCS")

def stop():
    manager.stop_all()
    manager.join_all()
