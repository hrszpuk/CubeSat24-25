import Vector.ADCS as adcs
import multiprocessing as mp

def start():
    pipeMain, pipeChild = mp.Pipe()
    p = mp.Process(target=adcs.start, args=(pipeChild,))
    p.start()

    pipeMain.send("health_check")
    print(pipeMain.recv())

    pipeMain.send("stop")

    p.join()
    pipeMain.close()