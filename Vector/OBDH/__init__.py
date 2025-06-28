from enums import Mode
from OBDH.main import OBDH

def start(mode=Mode.MANUAL):
    obdh = OBDH()

    match mode:
        case Mode.TEST:
            obdh.handle_input()
            pass
        case Mode.MANUAL:
            obdh.handle_input()
        case Mode.AUTO:
            #obdh.start_mission()
            pass