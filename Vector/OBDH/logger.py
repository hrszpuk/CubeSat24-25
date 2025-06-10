import logging
from logging.handlers import QueueListener
from multiprocessing import Queue

log_queue = Queue() # Send everything to the queue

file_handler = logging.FileHandler('vector.log') # Only want this to write stuff to the file
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

listener = QueueListener(log_queue, file_handler)
listener.start()

def get_logger():
    return log_queue
