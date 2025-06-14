from imu import Imu
from reaction_wheel import ReactionWheel
from sun_sensor import SunSensor
import time
import threading

class Adcs:
    def __init__(self):
        self.initialize_sun_sensors()
        self.initialize_orientation_system()

    def initialize_orientation_system(self):
        self.imu = Imu()
        self.reaction_wheel = ReactionWheel(self.imu)
        self.calibrate_orientation_system()

    def health_check(self, calibrate_orientation_system=False):
        health_check_text = ""
        errors = []

        # get the status of the IMU
        imu_health_check_text, imu_health_check, imu_errors = self.get_imu_health_check()
        health_check_text += imu_health_check_text
        errors.extend(imu_errors)

        # get the status of the sun sensors
        ss_health_check_text, ss_health_check, ss_errors = self.get_sun_sensors_health_check()
        health_check_text += ss_health_check_text
        errors.extend(ss_errors)
        
        # get the status of the reaction wheel
        rw_health_check_text = self.get_reaction_wheel_health_check()
        health_check_text += rw_health_check_text

        # check subsystem health
        if ss_health_check and imu_health_check:
            self.status = "OK"
            health_check_text += "STATUS: OK"
        else:
            self.status = "DOWN"
            health_check_text += "STATUS: DOWN - Error in one or more components"

        if calibrate_orientation_system:
            self.calibrate_orientation_system()
            #TODO sun sensors
        return health_check_text, errors

    def get_imu_health_check(self):
        health_check_text = ""
        is_component_ready = False
        errors = []

        data = self.imu.get_imu_data()
        gyroscope_data = data.get("gyroscope", None)
        orientation_data = data.get("orientation", None)
        errors = data.get("errors", [])

        if not gyroscope_data:
            gyroscope_text = "No data available"
            errors.append("Gyroscope data not available")
        else:
            gyroscope_text = f"X: {gyroscope_data[0]} º/s, Y: {gyroscope_data[1]} º/s, Z: {gyroscope_data[2]} º/s"

        if not orientation_data:
            orientation_text = "No data available"
            errors.append("Orientation data not available")
        else:
            orientation_text = f"X: {orientation_data[0]} º, Y: {orientation_data[1]} º, Z: {orientation_data[2]} º"

        health_check_text += f"Gyroscope: {gyroscope_text}\n"
        health_check_text += f"Orientation: {orientation_text}\n"

        if errors == []:
            is_component_ready = True

        return health_check_text, is_component_ready, errors

    def calibrate_orientation_system(self):
        imu_status = self.imu.get_status()
        if imu_status["status"] == "ACTIVE" and self.reaction_wheel is not None:
            print("IMU initialized successfully.")
            calibration_rotation_thread = threading.Thread(target=self.reaction_wheel.calibration_rotation)
            calibration_rotation_thread.start()
            self.imu.calibrate()
            calibration_rotation_thread.join()
        else:
            print(f"Orientation system calibration failed: Errors: {imu_status['errors']}")

    def initialize_sun_sensors(self):
        # Initialize the four sun sensors
        self.sun_sensors = [
            SunSensor(id=1, i2c_address=0x23, bus=1),
            SunSensor(id=2, i2c_address=0x5c, bus=1),
            SunSensor(id=3, i2c_address=0x23, bus=3),
            SunSensor(id=4, i2c_address=0x5c, bus=3),
        ]
        
    def get_sun_sensors_status(self):
        # Get the status of all sun sensors
        statuses = []
        for sensor in self.sun_sensors:
            status = sensor.get_status()
            statuses.append(status)
        return statuses

    def get_sun_sensors_health_check(self):
        health_check_text = ""
        is_component_ready = False
        errors = []

        sun_sensors_status = self.get_sun_sensors_status() 
        if not sun_sensors_status:
            health_check_text += "ERROR: No sun sensors found!\n"
        else:
            for sensor in sun_sensors_status:
                health_check_text += f"Mock Sun Sensor {sensor['id']}: {sensor['status']}\n"
                errors += sensor["errors"] if "errors" in sensor else []
                
        if errors == []:
            is_component_ready = True

        return health_check_text, is_component_ready, errors
    
    def get_reaction_wheel_health_check(self):
        # Get the status of the reaction wheel
        health_check_text = f"Reaction Wheel RPM: {self.reaction_wheel.get_current_speed():.2f}\n"
        return health_check_text
