import Vector.ADCS as adcs
import multiprocessing as mp

def start(manual = False):
    pipeMain, pipeChild = mp.Pipe()
    p = mp.Process(target=adcs.start, args=(pipeChild,))
    p.start()

    # TEST CODE
    if not manual:
        pipeMain.send("health_check")
        print(pipeMain.recv())
        pipeMain.send("stop")
    else:
        running = True
        while running:
            userInput = input("-> ")
            if userInput == "stop":
                running = False
            elif userInput == "health_check":
                pipeMain.send("health_check")
                print(pipeMain.recv())
                pipeMain.send("stop")

    p.join()
    pipeMain.close()
