import math
import threading
import time
from ADCS.brushless_motor import BrushlessMotor
from ADCS.brushed_motor import BrushedMotor
from ADCS.imu import Imu
import numpy as np
import math

# Satellite Variables
SAT_MASS = 1.576  # kg
SAT_SIDE1 = 0.1  # m
SAT_SIDE2 = 0.1  # m

# Actuator Variables
WHEEL_MASS = 0.1  # kg
WHEEL_RADIUS = 0.037605 # m
KT = 0.00955  # Motor torque constant (N·m/A)
KE = 0.00955  # Back-EMF constant (V·s/rad)
R = 0.09  # Motor resistance (Ohms)

class ReactionWheel:
    """
    A class to control a reaction wheel for attitude control in a satellite.
    This class uses PID control to adjust the wheel speed based on the satellite's orientation.
    Attributes:
        sat_mass (float): Mass of the satellite in kg.
        sat_side1 (float): Length of one side of the satellite in meters.
        sat_side2 (float): Length of another side of the satellite in meters.
        I_sat (float): Moment of inertia of the satellite.
        wheel_mass (float): Mass of the reaction wheel in kg.
        wheel_radius (float): Radius of the reaction wheel in meters.
        kt (float): Motor torque constant in N·m/A.
        ke (float): Back-EMF constant in V·s/rad.
        r (float): Motor resistance in Ohms.
        omega_sat (float): Angular velocity of the satellite in rad/s.
        omega_wheel (float): Angular velocity of the reaction wheel in rad/s.
        I_wheel (float): Moment of inertia of the reaction wheel.
        Imu (Imu): Instance of the IMU class for orientation data.
        motor_type (str): Type of motor used ("brushless" or "brushed").
        motor (BrushlessMotor or BrushedMotor): Instance of the motor class.
        desired_aligment (float): Desired aligment
        state (str): Current state of the reaction wheel.
    """
    def __init__(self, imu, motor_type="brushless"):
        # Satellite Parameters
        self.sat_mass = SAT_MASS
        self.sat_side1 = SAT_SIDE1
        self.sat_side2 = SAT_SIDE2
        self.I_sat = self.calculate_moment_of_inertia(self.sat_mass, self.sat_side1, self.sat_side2)

        # Actuator Parameters
        self.wheel_mass = WHEEL_MASS
        self.wheel_radius = WHEEL_RADIUS
        self.kt = KT
        self.ke = KE
        self.r = R
        self.omega_sat = 0.0
        self.omega_wheel = 0.0
        self.I_wheel = self.calculate_moment_of_inertia(self.wheel_mass, self.wheel_radius, I_type="wheel")

        # Only used for alignment with AprilTag
        self.desired_aligment = 0

        # IMU and Motor Initialization
        self.imu = imu
        self.motor_type = motor_type
        if self.motor_type == "brushless":
            # Initialize Brushless Motor
            self.motor = BrushlessMotor()
        else:
            self.motor = BrushedMotor()
            self.initial_yaw = self.imu.get_current_yaw()

        self.state = "STANDBY" # Initial state of the reaction wheel

        self.stop_event = threading.Event()
        
    def get_state(self):
        """
        Get the current state of the reaction wheel.
        Returns:
            str: Current state of the reaction wheel.
        """
        return self.state

    def set_state(self, state):
        """
        Set the current state of the reaction wheel.
        Parameters:
            state (str): New state of the reaction wheel.
        """
        self.state = state    
    
    def get_current_speed(self):
        """
        Get the current speed of the reaction wheel.
        Returns:
            float: Current speed in RPM.
        """
        return self.motor.get_current_speed()
    
    def pid_controller(self, setpoint, kp, ki, kd, previous_error=0, integral=0, dt=0.1):
        # Ensure PID gains are floats
        kp = float(kp)
        ki = float(ki)
        kd = float(kd)
        error = setpoint - self.imu.get_current_yaw() # This is PV
        integral += error * dt
        derivative = (error - previous_error) / dt
        control = kp * error + ki * integral + kd * derivative
        return control, error, integral


    def calculate_moment_of_inertia(self, mass, side1=0.1, side2=0.1, I_type="sat"):
        if I_type == "sat":
            """
            The moment of inertia (I) of a rectangular prism about 
            an axis through its center of mass is given by:
            I = (1/12) * m * (a^2 + b^2)
            """
            return 1/12 * mass * (side1**2 + side2**2)
        elif I_type == "wheel":
            """
            Calculate the moment of inertia for a disk flywheel.
            I = 1/2 * m * r
            """
            return 0.5 * mass * (side1)
        
    def normalize_angle(self, angle):
        return (angle % 360) - 180  # Ensures angle is within [-180, 180)

    def activate_wheel_brushed(self, setpoint, kp=1.8, ki=0.05, kd=0.1, t=5, tolerance=10, break_on_target=True):
        """
        Activate the reaction wheel to adjust the satellite's orientation.
        Parameters: 
            - setpoint: Target yaw angle (degrees/radians).
        """
        # Initialize PID variables
        previous_error = 0
        integral = 0
        dt = 0.1  # Time step in seconds
        omega_wheel = 0  # Initialize angular velocity

        print(f"Initial Yaw: {self.initial_yaw}")

        initial_setpoint = setpoint % 360
        saturated_attempts = 0
        target_achieved_attempts = 0
        stop_t = None  # Initialize stop time

        self.set_state("ROTATING")  # Set state to rotating

        while self.get_state() == "ROTATING" or not self.stop_event.is_set():
            pv = self.imu.get_current_yaw()

            # Get current yaw and compute PID control
            control, error, integral = self.pid_controller(
                setpoint, kp, ki, kd, previous_error, integral, dt
            )

            # Calculate new satellite and wheel angles
            new_pv = pv + control * dt
            angle_delta_sat = new_pv - pv
            angle_delta_wheel = -self.I_sat / self.I_wheel * angle_delta_sat

            # Update angular velocities
            new_omega_wheel = angle_delta_wheel / dt
            alpha_wheel = (new_omega_wheel - omega_wheel) / dt
            omega_wheel = -new_omega_wheel

            rpm = omega_wheel * 60 / (2 * math.pi)

            rpm = np.clip(rpm, -250, 250)  # Cap RPM to a reasonable range

            duty_cycle = rpm / 2.5  # Assuming 250 RPM is 100% duty cycle
            
            # Ensure duty cycle stays within 0-100%
            duty_cycle = np.clip(duty_cycle, -100, 100)
            
            # Update motor speed
            self.motor.set_speed(duty_cycle)

            previous_error = error

            if (setpoint > pv + 360 or setpoint < pv - 360) and saturated_attempts < 3:
                print("Setpoint is too far from current yaw, adjusting degree.")
                turns = pv // 360
                setpoint = turns * 360 + initial_setpoint

            if abs(self.imu.get_current_angular_velocity()) < 2:
                if abs(duty_cycle) == 100 and abs(pv - setpoint) > tolerance:
                    print("Wheel may be saturated!")
                    saturated_attempts += 1
            if abs(pv - setpoint) < tolerance:
                target_achieved_attempts += 1
                
            if saturated_attempts > 2:
                print("WHEEL SATURATION")
                setpoint = setpoint - 360 * duty_cycle / 100
                saturated_attempts = 0  # Reset after handling saturation
            if target_achieved_attempts > 1:
                if stop_t is None:
                    stop_t = time.time()
                if break_on_target:
                    print("Target achieved, stopping wheel.")
                    break
                else:
                    if abs(time.time() - stop_t) > t:
                        print("Target achieved, stopping wheel after time limit.")
                        break

            # Logging
            print(f"Target: {setpoint:.1f}, Current: {pv:.1f}, Duty: {duty_cycle:.1f}%, output: {control}, Current Velocity: {self.imu.get_current_angular_velocity():.1f}, IN_TARGET: {abs(pv - setpoint) < tolerance}")
            
            time.sleep(dt)
        self.stop_reaction_wheel()  # Stop the reaction wheel after rotation
        self.stop_event.clear()  # Clear the stop event to allow future operations

    def activate_wheel_brushless(self, setpoint, kp=0.4, ki=0, kd=0, t=5, tolerance=10, break_on_target=True):
        """
        Activate the reaction wheel to adjust the satellite's orientation.
        Parameters: 
            - setpoint: Target yaw angle (degrees/radians).
        """
        # Initialize PID variables
        previous_error = 0
        integral = 0
        dt = 0.1  # Time step in seconds
        omega_wheel = 0  # Initialize angular velocity

        initial_setpoint = setpoint % 360
        saturated_attempts = 0
        target_achieved_attempts = 0
        stop_t = None  # Initialize stop time

        self.set_state("ROTATING")  # Set state to rotating

        while self.get_state() == "ROTATING" or not self.stop_event.is_set():
            pv = self.imu.get_current_yaw()

            # Get current yaw and compute PID control
            control, error, integral = self.pid_controller(
                setpoint, kp, ki, kd, previous_error, integral, dt
            )

            # Calculate new satellite and wheel angles
            new_pv = pv + control * dt
            angle_delta_sat = new_pv - pv
            angle_delta_wheel = -self.I_sat / self.I_wheel * angle_delta_sat

            # Update angular velocities
            new_omega_wheel = angle_delta_wheel / dt
            alpha_wheel = (new_omega_wheel - omega_wheel) / dt
            omega_wheel = -new_omega_wheel

            rpm = omega_wheel * 60 / (2 * math.pi)

            rpm = np.clip(rpm, -7400, 7400)  # Cap RPM to a reasonable range

            duty_cycle = rpm / 74  # Assuming 250 RPM is 100% duty cycle
            
            # Ensure duty cycle stays within 0-100%
            duty_cycle = np.clip(duty_cycle, -15, 15)
            
            # Update motor speed
            self.motor.set_speed(duty_cycle)

            previous_error = error

            if (setpoint > pv + 360 or setpoint < pv - 360) and saturated_attempts < 3:
                print("Setpoint is too far from current yaw, adjusting degree.")
                turns = pv // 360
                setpoint = turns * 360 + initial_setpoint

            if abs(self.imu.get_current_angular_velocity()) < 2:
                if abs(duty_cycle) == 100 and abs(pv - setpoint) > tolerance:
                    print("Wheel may be saturated!")
                    saturated_attempts += 1
            if abs(pv - setpoint) < tolerance:
                target_achieved_attempts += 1
                
            if saturated_attempts > 2:
                print("WHEEL SATURATION")
                setpoint = setpoint - 360 * duty_cycle / 100
                saturated_attempts = 0  # Reset after handling saturation
            if target_achieved_attempts > 1:
                if stop_t is None:
                    stop_t = time.time()
                if break_on_target:
                    print("Target achieved, stopping wheel.")
                    break
                else:
                    if abs(time.time() - stop_t) > t:
                        print("Target achieved, stopping wheel after time limit.")
                        break

            # Logging
            print(f"Target: {setpoint:.1f}, Current: {pv:.1f}, Duty: {duty_cycle:.1f}%, output: {control}, Current Velocity: {self.imu.get_current_angular_velocity():.1f}, IN_TARGET: {abs(pv - setpoint) < tolerance}")
            
            time.sleep(dt)
        self.stop_reaction_wheel()  # Stop the reaction wheel after rotation
        self.stop_event.clear()  # Clear the stop event to allow future operations

    def activate_wheel_brushed_to_align(self, last_speed):
        """
        Activate the reaction wheel to align the satellite with a target orientation.
        Parameters:
            - last_speed: Last known speed of the reaction wheel.
        """

        # Initialize PID variables
        previous_error = 0
        integral = 0
        dt = 0.1  # Time step in seconds

        # PID Parameters
        kp = 2  # Proportional gain
        ki = 0.05  # Integral gain
        kd = 0.01  # Derivative gain
        setpoint = last_speed + self.desired_aligment

        self.set_state("ALIGNING")  # Set state to aligning

        while self.get_state() == "ALIGNING" and not self.stop_event.is_set():
            # Get current yaw and compute PID control
            pv = self.get_current_speed()  # Get current speed from the motor
            control, error, integral = self.pid_controller(
                setpoint, kp, ki, kd, previous_error, integral, dt
            )
            
            output = math.tanh(control * dt) * 100

            output = min(output, 100)
            output = max(output, -100)
            
            # Cap output to motor's operational range and convert to duty cycle (0-100%)
            duty_cycle = (output / 100) * 100
            
            # Update motor speed
            self.motor.set_speed(duty_cycle)
            
            # Logging (optional)
            print(f"Target: {setpoint:.2f}, Current: {pv:.2f}, Duty: {duty_cycle:.1f}%")
            previous_error = error

            time.sleep(dt)

        self.stop_reaction_wheel()  # Stop the reaction wheel after rotation
        self.stop_event.clear()  # Clear the stop event to allow future operations

    def get_status(self):
        """
        Get the status of the reaction wheel and IMU.
        Returns:
            dict: Status information including errors if any.
        """
        return self.motor.get_current_speed()
    
    # def calibration_rotation(self):
    #     """Perform a calibration rotation."""
    #     # Test motor from 50% to 100% throttle
    #     for percent in range(0, -101, -10):
    #         self.motor.set_speed(percent)
    #         time.sleep(2)
        
    #     for percent in range(-100, 0, 10):
    #         self.motor.set_speed(percent)
    #         time.sleep(2)

    def calibration_rotation(self):
        """Perform a calibration rotation."""
        # Test motor from 50% to 100% throttle
        for percent in range(0, -101, -10):
            self.motor.set_speed(percent)
            time.sleep(1)
        
        for percent in range(-100, 0, 10):
            self.motor.set_speed(percent)
            time.sleep(1)

        self.motor.stop()  # Stop the motor

    def stop_reaction_wheel(self):
        """
        Stop the reaction wheel.
        """
        self.motor.stop()
        self.set_state("STANDBY")
        self.stop_event.set()

    def brushless_compensation(self):
        while True:
            self.motor.set_speed(5)

        # def old_activate_wheel_with_speed_desired(self, setpoint = 20):
    #     """
    #     Activate the reaction wheel to rotate the satellite at a specified speed.
    #     Parameters:
    #         - speed: Speed in deg/s
    #     """
        
    #     # Initialize PID variables
    #     previous_error = 0
    #     integral = 0
    #     dt = 0.1  # Time step in seconds

    #     # PID Parameters
    #     kp = 2  # Proportional gain
    #     ki = 0.1  # Integral gain
    #     kd = 0.05  # Derivative gain

    #     self.set_state("ROTATING")  # Set state to rotating

    #     while self.get_state() == "ROTATING" or not self.stop_event.is_set():
    #         # Get current yaw and compute PID control
    #         pv = self.imu.get_current_angular_velocity()
    #         control, error, integral = self.pid_controller(
    #             setpoint, kp, ki, kd, previous_error, integral, dt
    #         )

    #         output = control * dt

    #         output = min(output, 100)
    #         output = max(output, 0)
            
    #         # Cap output to motor's operational range and convert to duty cycle (0-100%)
    #         duty_cycle = (output / 100) * 100
            
    #         # Update motor speed
    #         self.motor.set_speed(duty_cycle)
            
    #         # Logging (optional)
    #         print(f"Target: {setpoint:.2f}, Current: {pv:.2f}, Duty: {duty_cycle:.1f}%")
    #         previous_error = error

    #         time.sleep(dt)
    #     self.stop_reaction_wheel()  # Stop the reaction wheel after rotation