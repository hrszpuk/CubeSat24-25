import RPi.GPIO as GPIO
import time

in3 = 17  # GPIO17 - Connect to L298N IN3
in4 = 22  # GPIO27 - Connect to L298N IN4
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

    def get_current_speed(self, return_percentage=False):
        if return_percentage:
            return (self.current_speed / MAX_RPM) * 100
        return self.current_speed
    
    def start(self):
        GPIO.output(in3, GPIO.HIGH)
        GPIO.output(in4, GPIO.LOW)
        self.motor.start(self.current_speed)
    
    def set_speed(self, speed_percentage):
        # Stop the motor briefly before changing direction
        if (speed_percentage >= 0 and self.current_speed < 0) or (speed_percentage < 0 and self.current_speed >= 0):
            self.motor.ChangeDutyCycle(0)
            time.sleep(0.1)  # Short delay to allow motor to stop
        
        # Set direction
        if speed_percentage >= 0:
            GPIO.output(in3, GPIO.HIGH)
            GPIO.output(in4, GPIO.LOW)
            duty = speed_percentage
        else:
            GPIO.output(in3, GPIO.LOW)
            GPIO.output(in4, GPIO.HIGH)
            duty = -speed_percentage
        
        # Apply new speed
        self.motor.ChangeDutyCycle(min(max(duty, 0), 100))
        self.current_speed = (speed_percentage / 100.0) * MAX_RPM

    def stop(self):
        self.set_speed(0)

if __name__ == "__main__":
    motor = BrushedMotor()
    try:
        # while True:
        #     for speed in range(-100, 101, 10):  # Increase speed from 0% to 100%
        #         motor.set_speed(speed)
        #         print(f"Speed set to {speed}%")
        #         time.sleep(1)
        while True:
            motor.set_speed(100)  # Set speed to 50%
    except KeyboardInterrupt:
        pass