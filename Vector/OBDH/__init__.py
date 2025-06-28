from enums import Mode
from OBDH.main import OBDH


def start(mode=Mode.MANUAL):
    obdh = OBDH()

    if mode == Mode.MANUAL:
        obdh.handle_input()
    else:
        obdh.start_mission()
