"""
Start up script
"""
from OBDH import start
from enums import Mode
#from TTC import start

import multiprocessing as mp

if __name__ == '__main__':
    start(Mode.TEST)
