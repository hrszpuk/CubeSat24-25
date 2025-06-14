from Vector.ADCS.adcs import Adcs

def start(pipe):
    theGhostOfTheGoon = Adcs()

    running = True
    while running:
        line = pipe.recv()
        if line == "health_check":
            variable = theGhostOfTheGoon.health_check()
            pipe.send(variable)
        elif line == "stop":
            running = False
