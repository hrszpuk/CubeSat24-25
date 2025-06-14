
from adcs import Adcs


def start(pipe):
    pass

def stop():
    pass

adcs = Adcs()
adcs_health_check_text, adcs_errors = adcs.health_check()
print(adcs_health_check_text)
if adcs_errors:
    print("Errors found during health check:")
    for error in adcs_errors:
        print(error)
adcs.calibrate_imu()