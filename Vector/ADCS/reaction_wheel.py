import time
from ADCS.brushless_motor import BrushlessMotor
from ADCS.brushed_motor import BrushedMotor
from ADCS.imu import Imu
import numpy as np

# Satellite Variables
SAT_MASS = 1.5  # kg
SAT_SIDE1 = 0.1  # m
SAT_SIDE2 = 0.1  # m

# Actuator Variables
WHEEL_MASS = 0.1  # kg
WHEEL_RADIUS = 0.0375  # m
KT = 0.00955  # Motor torque constant (N·m/A)
KE = 0.00955  # Back-EMF constant (V·s/rad)
R = 0.09  # Motor resistance (Ohms)

# PID Variables
KP = 2  # Proportional gain
KI = 0.05  # Integral gain
KD = 0.01  # Derivative gain

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

        # IMU and Motor Initialization
        self.imu = imu
        self.motor_type = motor_type
        if self.motor_type == "brushless":
            # Initialize Brushless Motor
            self.motor = BrushlessMotor()
        else:
            self.motor = BrushedMotor()

    def get_current_speed(self):
        """
        Get the current speed of the reaction wheel.
        Returns:
            float: Current speed in RPM.
        """
        return self.motor.get_current_speed()

    def pid_controller(self, setpoint, kp, ki, kd, previous_error=0, integral=0, dt=0.1):
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
        
    def activate_wheel(self, setpoint):
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

        initial_yaw = self.imu.get_current_yaw()
        turns = initial_yaw // 360
        setpoint = setpoint + (turns * 360)  # Adjust setpoint to the same turn as initial_yaw
        
        while True:  # Replace with your termination condition
            # Get current yaw and compute PID control
            pv = self.imu.get_current_yaw()
            control, error, integral = self.pid_controller(
                setpoint, KP, KI, KD, previous_error, integral, dt
            )

            # Calculate new satellite and wheel angles
            new_pv = pv + control * dt
            angle_delta_sat = new_pv - pv
            angle_delta_wheel = -self.I_sat / self.I_wheel * angle_delta_sat

            # Update angular velocities
            new_omega_wheel = angle_delta_wheel / dt
            alpha_wheel = (new_omega_wheel - omega_wheel) / dt
            omega_wheel = new_omega_wheel

            # Convert to motor voltage (simplified for unidirectional ESC)
            voltage = (R * self.I_wheel * alpha_wheel) / self.kt + self.ke * omega_wheel
            
            # Cap voltage to motor's operational range and convert to duty cycle (0-100%)
            voltage = np.clip(voltage, 0, self.motor.v)  # Force positive voltage
            duty_cycle = (voltage / self.motor.v) * 100  # 0-100% range
            
            # Ensure duty cycle stays within 0-100%
            duty_cycle = np.clip(duty_cycle, 0, 100)
            
            # Update motor speed
            self.motor.set_speed(duty_cycle)
            
            # Logging (optional)
            print(f"Target: {setpoint:.2f}, Current: {pv:.2f}, Duty: {duty_cycle:.1f}%")
            
            time.sleep(dt)

    def activate_wheel_with_speed_desired(self, speed = 20):
        """
        Activate the reaction wheel to rotate the satellite at a specified speed.
        Parameters:
            - speed: Speed in deg/s
        """
        
        initial_yaw = self.imu.get_current_yaw()
        target_yaw = initial_yaw + 360

        while self.imu.get_current_yaw() >= target_yaw:
            pass
        
    def get_status(self):
        """
        Get the status of the reaction wheel and IMU.
        Returns:
            dict: Status information including errors if any.
        """
        return self.motor.get_current_speed()
    
    def calibration_rotation(self):
        """Perform a calibration rotation."""
        # Test motor from 50% to 100% throttle
        for percent in range(20, 61, 10):
            self.motor.set_speed(percent)
            time.sleep(2)

        self.motor.stop()  # Stop the motor

        #print("Calibration rotation complete. Motor stopped.")

        # # Ramp down
        # for percent in range(40, 0, -10):
        #     self.motor.set_speed(percent)
        #     time.sleep(3)