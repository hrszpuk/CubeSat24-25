import logging
import pickle


class TTCHandler(logging.Handler):
    def __init__(self, pipe_conn):
        super().__init__()
        self.pipe_conn = pipe_conn

    def emit(self, record):
        try:
            s = self.format(record)
            self.pipe_conn.send(("log", s))
        except Exception:
            self.handleError(record)

