import asyncio
from TTC.main import TTC

event_loop = asyncio.get_event_loop()

def start(pipe, log_queue):
    ttc = TTC(pipe, event_loop, log_queue)
    ttc.log("Starting subsystem...")
    event_loop.run_until_complete(ttc.start_server())
    event_loop.run_in_executor(None, ttc.handle_obdh_instructions)
    event_loop.run_forever()