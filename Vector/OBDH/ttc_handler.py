import logging
from multiprocessing import *

class TTCHandler(logging.Handler):
    def __init__(self, pipe_conn, command):
        super().__init__()
        self.pipe_conn = pipe_conn
        self.command = command

    def emit(self, record):
        try:
            s = self.format(record)
            self.pipe_conn.send((self.command, {"message": s}))
        except Exception:
            self.handleError(record)
