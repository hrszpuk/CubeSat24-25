import logging
from multiprocessing import *
from enums import TTCState

class TTCHandler(logging.Handler):
    def __init__(self, pipe_conn):
        super().__init__()
        self.pipe_conn = pipe_conn

    def emit(self, record):
        try:
            self.pipe_conn.send(("get_state", {}))
            ttc_state = self.pipe_conn.recv()

            if ttc_state == TTCState.CONNECTED:
                s = self.format(record)
                self.pipe_conn.send(("log", {"message": s}))
        except Exception:
            self.handleError(record)