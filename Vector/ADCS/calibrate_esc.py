from gpiozero import PWMOutputDevice
import time

PIN = 26  # GPIO26
motor = PWMOutputDevice(PIN, frequency=50)  # 50Hz for ESC

# def set_speed(percent):
#     duty_cycle = 5 + (percent * 0.05)  # 0% → 5%, 100% → 10%
#     motor.value = duty_cycle / 100
#     print(f"Speed: {percent}% (Duty: {duty_cycle}%)")

MIN_PW = 1.10   # in ms
MAX_PW = 1.90   # in ms
PERIOD = 20.0   # ms for 50Hz

def set_speed(percent):
    pw = MIN_PW + (MAX_PW - MIN_PW) * (percent / 100.0)
    duty = (pw / PERIOD) * 100.0
    motor.value = duty / 100.0
    print(f"{percent:>3}% → {pw:.2f} ms ({duty:.2f}% duty)")


try:
    # Step 1: Send MAX throttle (2000µs = 10%) *before powering ESC*
    print("Disconnect battery. Set to 100% throttle, then power on ESC.")
    set_speed(100)  # 10% duty cycle (2000µs)
    time.sleep(2)

    # Step 2: Power on ESC (wait for beeps)
    input("Connect battery NOW. Wait for beeps, then press Enter...")

    # Step 3: Send MIN throttle (1000µs = 5%)
    set_speed(0)  # 5% duty cycle (1000µs)
    time.sleep(5)  # Wait for confirmation beeps

    # Step 4: Test
    print("Calibration done! Testing...")
    for percent in [0, 50, 100, 50, 0]:
        set_speed(percent)
        time.sleep(3)

except KeyboardInterrupt:
    pass
finally:
    set_speed(0)  # Return to idle
    print("Done.")