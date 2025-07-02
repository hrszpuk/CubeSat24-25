import logging
import sys
from datetime import datetime
from OBDH.ttc_handler import TTCHandler

class Logger:
    def __init__(self, log_to_console=True, log_file="vector", ttc_pipe=None):
        self.logger = logging.getLogger("Vector")
        self.logger.setLevel(logging.DEBUG)

        # Prevent adding handlers multiple times
        if not self.logger.handlers:
            self.formatter = logging.Formatter('%(asctime)s - %(processName)s - %(levelname)s - %(message)s')

            timestamp = datetime.now().strftime("%Y-%m%-d-T%H-%M-%S")
            filename = f"vector_{timestamp}.log"

            # File handler
            file_handler = logging.FileHandler(filename)
            file_handler.setFormatter(self.formatter)
            self.logger.addHandler(file_handler)

            # Console handler
            if log_to_console:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(self.formatter)
                self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger

    def set_ttc_handler(self, ttc_pipe, command):
        ttc_handler = TTCHandler(ttc_pipe, command)
        ttc_handler.setFormatter(self.formatter)
        self.logger.addHandler(ttc_handler)
