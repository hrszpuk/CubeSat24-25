from gpiozero import Motor
from gpiozero.tools import absoluted
import time

in3 = 17  # GPIO17 - Connect to L298N IN3
in4 = 22  # GPIO27 - Connect to L298N IN4
en_b = 23 # GPIO23 - Connect to L298N ENB

MAX_RPM = 250

class BrushedMotor:
    def __init__(self):
        self.motor = Motor(in3, in4, enable=en_b)
        self.rpm = 0

    def get_current_speed(self):
        return self.rpm
    
    def forward(self, speed):
        self.motor.forward(speed)

    def backward(self, speed):
        self.motor.backward(speed)
    
    def set_speed(self, speed_percentage):
        # Stop the motor briefly before changing direction
        if (speed_percentage >= 0 and self.motor.value < 0) or (speed_percentage < 0 and self.motor.value >= 0):
            self.stop()
            time.sleep(0.1)  # Short delay to allow motor to stop
        
        # Set direction
        if speed_percentage >= 0:
            self.forward(speed_percentage / 100)
        else:
            self.backward(speed_percentage / 100)
        
        # Update rpm
        self.rpm = absoluted(self.motor.value) * MAX_RPM

    def reverse(self):
        self.motor.reverse()

    def stop(self):
        self.motor.stop()

if __name__ == "__main__":
    motor = BrushedMotor()
    
    try:
        while True:
            motor.forward(1)
    except KeyboardInterrupt:
        pass