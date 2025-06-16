import logging
import sys

class Logger:
    def __init__(self, log_to_console=True, log_file="vector.log"):
        self.logger = logging.getLogger("Vector")
        self.logger.setLevel(logging.DEBUG)

        # Prevent adding handlers multiple times
        if not self.logger.handlers:
            formatter = logging.Formatter('%(asctime)s - %(processName)s - %(levelname)s - %(message)s')

            # File handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            # Console handler
            if log_to_console:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(formatter)
                self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger