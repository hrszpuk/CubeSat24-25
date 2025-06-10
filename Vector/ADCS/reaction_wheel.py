from imu import Imu

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
    def __init__(self):
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

        # IMU Initialization
        self.Imu = Imu()
    
    def get_orientation(self):
        pitch, roll, yaw = self.Imu.get_orientation()
        return yaw

    def pid_controller(self, setpoint, kp, ki, kd, previous_error=0, integral=0, dt=0.1):
        error = setpoint - self.get_orientation() # This is PV
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