from enum import Enum
from OBDH.main import OBDH

Mode = Enum("Mode", [("TEST", 0), ("MANUAL", 1), ("AUTO", 2)])

def start(mode=Mode.MANUAL):
    obdh = OBDH()

    if mode == Mode.MANUAL:
        obdh.handle_input()
    else:
        obdh.start_mission()