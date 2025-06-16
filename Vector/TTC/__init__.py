from TTC.main import TTC

ttc = TTC()
ttc.start()

while not ttc.get_connection():
    ttc.connect()

ttc.echo()

def start(pipe, log_queue):
    log_queue.put(("TTC", "Starting Subsystem"))

    return
