from OBDH.process_manager import ProcessManager
from OBDH.logger import get_logger
from ADCS import start as adcs_start

manager = ProcessManager()

def start():
    manager.add_process(name="ADCS", target=adcs_start)

def stop():
    manager.stop_all()
    manager.join_all()
