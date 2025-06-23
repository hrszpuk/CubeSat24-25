from TTC.main import TTC

def start(pipe, log_queue):
    ttc = TTC(log_queue)
    ttc.start()

    while ttc.get_status():
        command, args = pipe.recv()
