import asyncio
from TTC.main import TTC
from TTC.testttc import TestTTC

event_loop = asyncio.get_event_loop()

def start(pipe, log_queue):
    ttc = TTC(pipe, event_loop, log_queue)
    ttc.log("Starting subsystem...")
    ttc.start_obdh_listener()
    event_loop.run_until_complete(ttc.start_server())
    event_loop.run_forever()

def start_test():
    ttc = TestTTC(event_loop)
    ttc.log("Starting subsystem...")
    event_loop.run_until_complete(ttc.start_server())
    event_loop.run_forever()