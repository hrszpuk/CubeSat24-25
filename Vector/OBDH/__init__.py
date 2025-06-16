import Vector.ADCS as adcs
import Vector.Payload as payload
import multiprocessing as mp

def start(manual=False):
    pipeMain_adcs, pipeChild_adcs = mp.Pipe()
    pipeMain_payload, pipeChild_payload = mp.Pipe()

    p_adcs = mp.Process(target=adcs.start, args=(pipeChild_adcs,))
    p_payload = mp.Process(target=payload.start, args=(pipeChild_payload,))

    p_adcs.start()
    p_payload.start()

    # TEST CODE
    if not manual:
        pipeMain_adcs.send("health_check")
        print("ADCS:", pipeMain_adcs.recv())
        pipeMain_adcs.send("stop")

        pipeMain_payload.send("health_check")
        print("Payload:", pipeMain_payload.recv())
        pipeMain_payload.send("stop")
    else:
        running = True
        while running:
            userInput = input("-> ")
            if userInput == "stop":
                running = False
            elif userInput == "health_check":
                pipeMain_adcs.send("health_check")
                print("ADCS:", pipeMain_adcs.recv())
                pipeMain_adcs.send("stop")

                pipeMain_payload.send("health_check")
                print("Payload:", pipeMain_payload.recv())
                pipeMain_payload.send("stop")

    p_adcs.join()
    p_payload.join()
    pipeMain_adcs.close()
    pipeMain_payload.close()
