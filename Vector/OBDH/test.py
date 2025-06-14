import multiprocessing as mp
import time

def childProcess(pipe):
    running = True
    while running:
        line = pipe.recv()
        if line == "ping":
            pipe.send("pong")
        elif line == "exit":
            running = False

def masterProcess():
    pipeMain, pipeChild = mp.Pipe()
    p = mp.Process(target=childProcess, args=(pipeChild,))
    p.start()

    time.sleep(0.5)
    pipeMain.send("ping")
    print(pipeMain.recv())

    pipeMain.send("exit")

    p.join()
    pipeMain.close()

print("tehehehe")
masterProcess()
print("yeheehehe")