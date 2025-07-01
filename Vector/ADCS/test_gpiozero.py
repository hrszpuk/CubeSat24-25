import gpiozero as GPIO
import time

in3 = 17  # GPIO17 - Connect to L298N IN3
in4 = 22  # GPIO27 - Connect to L298N IN4
en_b = 23 # GPIO23 - Connect to L298N ENB

MAX_RPM = 250
    
if __name__ == "__main__":
    motor = GPIO.Motor(in3, in4, enable=en_b)

    while True:
        motor.forward(0.5)
        motor.backward(0.5)