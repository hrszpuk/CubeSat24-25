from adcs import Adcs

def start():
    Adcs()

def stop():
    pass

if __name__ == "__main__":
    start()  # This will be called when run as subprocess
    try:
        while True:  # Keep process running
            pass
    except KeyboardInterrupt:
        stop()
