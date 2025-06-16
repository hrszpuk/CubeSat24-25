from ADCS.adcs_controller import AdcsController

def start(pipe):
    adcs_controller = AdcsController()
    
    running = True
    while running:
        line = pipe.recv()
        if line == "health_check":
            variable = adcs_controller.health_check()
            pipe.send(variable)
        elif line == "stop":
            running = False
