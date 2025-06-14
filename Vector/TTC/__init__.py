from main import TTC

ttc = TTC()
ttc.start()

while not ttc.get_connection():
    ttc.connect()

ttc.echo()

def start(pipe):
    pass

def stop():
    pass
