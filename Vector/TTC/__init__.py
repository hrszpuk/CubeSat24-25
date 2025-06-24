import asyncio
from TTC.main import TTC
from TTC.process_manager import ProcessManager

processes = ProcessManager()
event_loop = asyncio.get_event_loop()

def start(obdh_pipe, log_queue):
    ttc = TTC(obdh_pipe, log_queue)
    ttc.log("Starting subsystem...")
    processes.set_logfn(ttc.log)
    processes.start("ground_communications", ground_comms, ttc, obdh_pipe)
    processes.start("obdh_communications", obdh_comms, ttc, obdh_pipe)

def ground_comms(ttc, obdh_pipe):
    event_loop.run_until_complete(ttc.start_server())
    event_loop.run_forever()

def obdh_comms(ttc, obdh_pipe):
    running = True

    while running:
        command, args = obdh_pipe.recv()
        ttc.log(f"Received command from OBDH: {command} with arguments {args}")

        match command:
            case "health_check":
                try:
                    health_check = ttc.health_check()
                    obdh_pipe.send(health_check)
                except Exception as err:
                    ttc.log(f"[ERROR] Failed to process command ({command}) from OBDH: {err}")
            case "send_message":
                msg = args["message"]
                
                try:
                    ttc.send_message(msg)
                except Exception as err:
                    ttc.log(f"[ERROR] Failed to process command ({command}) from OBDH: {err}")
            case "send_file":
                path = args["path"]

                try:
                    ttc.send_file(path)
                except Exception as err:
                    ttc.log(f"[ERROR] Failed to process command ({command}) from OBDH: {err}")
            case "stop":
                print("stop signal received")
                pass
            case _:
                ttc.log(f"Invalid command received from OBDH: {command}")