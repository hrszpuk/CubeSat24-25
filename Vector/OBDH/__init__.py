import Vector.OBDH.process_manager as pm

def start(manual=False):
    processManager = pm.ProcessManager()
    processManager.start_all()

    if not manual:
        processManager.send(pm.ADCS_PROCESS, "health_check")
        print(processManager.recv(pm.ADCS_PROCESS))
        processManager.send(pm.ADCS_PROCESS, "stop")
    else:
        running = True
        while running:
            userInput = input("-> ")
            if userInput == "stop":
                processManager.send(pm.ADCS_PROCESS, "stop")
                running = False
            elif userInput == "health_check":
                processManager.send(pm.ADCS_PROCESS, "health_check")
                print(processManager.recv(pm.ADCS_PROCESS))

    processManager.join_all()
