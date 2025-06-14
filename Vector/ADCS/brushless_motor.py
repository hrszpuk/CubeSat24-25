from gpiozero import PWMOutputDevice
import time

KV = 1000  # Motor constant (RPM/V)
V = 7.4  # Supply voltage (Volts)
PIN = 26  # GPIO26 (Physical Pin 37)

class BrushlessMotor:
    """
    A class to control a brushless motor (A2212/13T) using an ESC (Electronic Speed Controller).
    This class uses PWM to control the speed of the motor.
    Attributes:
        kv (int): Motor constant in RPM per Volt.
        v (float): Supply voltage in Volts.
        pin (int): GPIO pin number for the ESC.
        motor (PWMOutputDevice): PWM output device for controlling the ESC.
        current_speed (float): Current speed of the motor in RPM.
    """
    def __init__(self, kv=KV, v=V, pin=PIN):
        self.motor = PWMOutputDevice(PIN, frequency=50)  # 50Hz for ESC
        self.current_speed = 0  # Current speed in RPM
        self.kv = kv
        self.v = v

        self.arm_esc()

    def get_current_speed(self):
        """Get the current speed of the motor in RPM."""
        return self.current_speed
    
    def arm_esc(self):
        """Arm the ESC by sending a 1000µs pulse."""
        self.motor.value = 0.05  # 5% duty cycle = 1000µs
        time.sleep(2)
        self.motor.value = 0  # Stop sending signal

    def set_speed(self, speed_percentage):
        """Convert % (0-100) to ESC duty cycle (5%-10%)."""
        duty_cycle = 5 + (speed_percentage * 0.05)  # 0% = 5%, 100% = 10%
        self.motor.value = duty_cycle / 100
        self.current_speed = self.kv * self.v * speed_percentage

    def calibrate(self):
        """Calibrate the ESC by sending a full throttle signal."""
        try:
            # Step 1: Send MAX throttle (2000µs = 10%) *before powering ESC*
            print("Disconnect battery. Set to 100% throttle, then power on ESC.")
            self.set_speed(100)  # 10% duty cycle (2000µs)
            time.sleep(2)

            # Step 2: Power on ESC (wait for beeps)
            input("Connect battery NOW. Wait for beeps, then press Enter...")

            # Step 3: Send MIN throttle (1000µs = 5%)
            self.set_speed(0)  # 5% duty cycle (1000µs)
            time.sleep(5)  # Wait for confirmation beeps

        except KeyboardInterrupt:
            pass
        finally:
            self.set_speed(0)  # Return to idle
            print("Calibration done!")