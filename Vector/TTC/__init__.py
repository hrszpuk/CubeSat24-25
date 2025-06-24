from TTC.main import TTC

def start(pipe, log_queue):
    ttc = TTC(pipe, log_queue)
    ttc.start()

    while True:
        command, args = pipe.recv()

        match command:
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
            case _:
                ttc.log(f"Invalid command received from OBDH: {command}")