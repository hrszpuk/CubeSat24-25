from TTC.main import TTC

def start():
    ttc = TTC()
    ttc.start()
    ttc.get_status()

    while not ttc.get_connection():
        ttc.connect()

    ttc.await_message()

def start(log_queue):
    log_queue.put(("TTC", "Starting Subsystem"))

    return
