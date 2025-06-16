from TTC.main import TTC

ttc = TTC()
ttc.start()

while not ttc.get_connection():
    ttc.connect()

ttc.echo()

def start():
    pass

def stop():
    pass