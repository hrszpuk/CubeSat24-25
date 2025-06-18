from TTC.main import TTC

def start(pipe, log_queue):    
    ttc = TTC(log_queue)
    ttc.start()
    ttc.get_info()

    while not ttc.get_connection():
        ttc.connect()

    ttc.await_message()