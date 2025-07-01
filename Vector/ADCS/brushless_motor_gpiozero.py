from gpiozero import PWMOutputDevice
import time

KV = 1000
V = 7.4
PIN = 26
PWM_FREQUENCY = 50

MIN_PULSE_WIDTH_US = 1000
MAX_PULSE_WIDTH_US = 2000

def us_to_duty_cycle_rpi(pulse_width_us):
    pulse_width_us = max(MIN_PULSE_WIDTH_US, min(MAX_PULSE_WIDTH_US, pulse_width_us))
    duty_cycle = (pulse_width_us / 20000) * 100
    return duty_cycle

def set_speed(motor, speed_percentage):
    pulse_width_us = MIN_PULSE_WIDTH_US + (speed_percentage / 100) * (MAX_PULSE_WIDTH_US - MIN_PULSE_WIDTH_US)
    duty_cycle = us_to_duty_cycle_rpi(pulse_width_us)
    motor.value = int(duty_cycle)

    current_speed = KV * V * (speed_percentage / 100)
    if speed_percentage == 0:
        motor.off()
        
if __name__ == "__main__":
    motor = PWMOutputDevice(PIN, frequency=PWM_FREQUENCY)
    motor.value = us_to_duty_cycle_rpi(MIN_PULSE_WIDTH_US)