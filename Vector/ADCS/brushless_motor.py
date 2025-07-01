import RPi.GPIO as GPIO
import time

KV = 1000
V = 7.4
PIN = 26

PWM_FREQUENCY = 50

MIN_PULSE_WIDTH_US = 1000
MAX_PULSE_WIDTH_US = 2000

def us_to_duty_cycle_rpi(pulse_width_us):
    pulse_width_us = max(MIN_PULSE_WIDTH_US, min(MAX_PULSE_WIDTH_US, pulse_width_us))
    duty_cycle = (pulse_width_us / 20000.0) * 100.0
    return duty_cycle

class BrushlessMotor:
    def __init__(self, kv=KV, v=V, pin=PIN):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        self.motor = GPIO.PWM(pin, PWM_FREQUENCY)
        self.motor.start(us_to_duty_cycle_rpi(MIN_PULSE_WIDTH_US))
        self.current_speed = 0
        self.kv = kv
        self.v = v
        self.pin = pin

        #self.arm_esc()

    def get_current_speed(self):
        return self.current_speed
    
    def _set_pulse_us(self, pulse_width_us):
        duty_cycle = us_to_duty_cycle_rpi(pulse_width_us)
        self.motor.ChangeDutyCycle(duty_cycle)
    
    def arm_esc(self):
        self._set_pulse_us(MIN_PULSE_WIDTH_US)
        time.sleep(2)
        self._set_pulse_us(MIN_PULSE_WIDTH_US)

    def set_speed(self, speed_percentage):
        GPIO.setup(self.pin, GPIO.OUT)
        pulse_width_us = MIN_PULSE_WIDTH_US + (speed_percentage / 100.0) * (MAX_PULSE_WIDTH_US - MIN_PULSE_WIDTH_US)
        self._set_pulse_us(int(pulse_width_us))
        self.current_speed = self.kv * self.v * (speed_percentage / 100.0)
        if speed_percentage == 0:
            self.stop()

    def calibrate(self):
        try:
            print("Disconnect battery. Set to 100% throttle, then power on ESC.")
            self._set_pulse_us(MAX_PULSE_WIDTH_US)
            time.sleep(2)

            print("Connect battery NOW. Wait for beeps, then press Enter...")
            input()

            self._set_pulse_us(MIN_PULSE_WIDTH_US)
            time.sleep(5)

        except KeyboardInterrupt:
            pass
        finally:
            self._set_pulse_us(MIN_PULSE_WIDTH_US)
            print("Calibration done!")

    def stop(self):
        self._set_pulse_us(MIN_PULSE_WIDTH_US)
        GPIO.setup(self.pin, GPIO.LOW)
        time.sleep(0.5)
        
if __name__ == "__main__":
    motor = None
    try:
        motor = BrushlessMotor(pin=PIN)
        motor.calibrate()

        print("\n--- Example 1: Gradual Speed Change ---")
        for speed_pct in range(0, 101, 5):
            motor.set_speed(speed_pct)
            time.sleep(0.2)

        for speed_pct in range(100, -1, -5):
            motor.set_speed(speed_pct)
            time.sleep(0.2)
        
        motor.set_speed(0)
        time.sleep(1)

        print("\n--- Example 2: Manual Control ---")
        print("Enter a speed percentage (0-100). Type 'exit' or 'quit' to finish.")
        while True:
            try:
                user_input = input("Enter speed percentage (0-100): ").strip().lower()
                if user_input in ['exit', 'quit']:
                    break
                speed_pct = int(user_input)
                speed_pct = max(0, min(100, speed_pct))
                motor.set_speed(speed_pct)
            except ValueError:
                print("Invalid input. Please enter an integer (0-100), 'exit', or 'quit'.")
            except Exception as e:
                print(f"An error occurred: {e}")
                break

    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if motor:
            motor.stop()
        GPIO.cleanup()
        print("GPIO cleanup done.")
        print("Brushless motor control program finished.")