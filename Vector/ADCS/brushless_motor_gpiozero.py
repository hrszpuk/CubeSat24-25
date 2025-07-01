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
    duty_cycle = (pulse_width_us / 20000.0) * 100.0
    return duty_cycle
        
if __name__ == "__main__":
    motor = PWMOutputDevice(PIN, frequency=PWM_FREQUENCY)
    
    while True:
        motor.on()