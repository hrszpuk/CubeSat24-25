import RPi.GPIO as GPIO
import time

in3 = 17  # GPIO17 - Connect to L298N IN3
in4 = 27  # GPIO27 - Connect to L298N IN4
en_b = 23 # GPIO23 - Connect to L298N ENB

MAX_RPM = 250

class BrushedMotor:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(in3, GPIO.OUT)
        GPIO.setup(in4, GPIO.OUT)
        GPIO.setup(en_b, GPIO.OUT)

        self.motor = GPIO.PWM(en_b, 100)
        self.current_speed = 0
        self.start()

    def get_current_speed(self):
        return self.current_speed
    
    def start(self):
        GPIO.output(in3, GPIO.HIGH)
        GPIO.output(in4, GPIO.LOW)
        self.motor.start(self.current_speed)

    def set_speed(self, speed_percentage):
        self.motor.ChangeDutyCycle(speed_percentage)
        self.current_speed = speed_percentage / 100.0 * MAX_RPM

    def stop(self):
        self.set_speed(0)