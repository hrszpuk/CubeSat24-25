from ADCS.imu import Imu
from ADCS.reaction_wheel import ReactionWheel
from ADCS.sun_sensor import SunSensor
import time
import threading
import queue
import numpy as np

class AdcsController:
    def __init__(self, log_queue):
        self.initialize_sun_sensors()
        self.initialize_orientation_system()
        self.calibrating_orientation_system = False

        self.log_queue = log_queue

    def log(self, msg):
        self.log_queue.put(("ADCS", msg))

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
            self.log("IMU initialized successfully.")
            self.calibrating_orientation_system = True
            readings_queue = queue.Queue()

            calibration_rotation_thread = threading.Thread(target=self.reaction_wheel.calibration_rotation)
            calibration_rotation_thread.start()
            self.imu.calibrate()
            calibration_rotation_thread.join()

            sun_sensor_measurement_thread = threading.Thread(target=self.sun_sensor_calibration_measurement, args=(readings_queue,))
            sun_sensor_measurement_thread.start()
            self.reaction_wheel.calibration_rotation()
            self.calibrating_orientation_system = False
            sun_sensor_measurement_thread.join()
            
            readings = readings_queue.get()

            if readings is not None and len(readings) > 0:
                max_index = np.argmax(readings)
                max_value = readings[max_index]
                print(f"MAX YAW: {max_index}°, MAX VALUE: {max_value}")
                print("CALIBRATION ORIENTATION SYSTEM COMPLETE\n\n")
                self.imu.set_calibration_offset(max_index)
            else:
                print("No readings available to determine max.")

        else:
            print(f"Orientation system calibration failed: Errors: {imu_status['errors']}")

    def initialize_sun_sensors(self):
        # Initialize the four sun sensors
        self.sun_sensors = [
            SunSensor(id=0, i2c_address=0x23, bus=1),
            SunSensor(id=1, i2c_address=0x5c, bus=1),
            SunSensor(id=2, i2c_address=0x23, bus=3),
            SunSensor(id=3, i2c_address=0x5c, bus=3),
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
                health_check_text += f"Sun Sensor {sensor['id']}: {sensor['status']}\n"
                errors += sensor["errors"] if "errors" in sensor else []
                
        if errors == []:
            is_component_ready = True

        return health_check_text, is_component_ready, errors
    
    def get_reaction_wheel_health_check(self):
        # Get the status of the reaction wheel
        health_check_text = f"Reaction Wheel RPM: {self.reaction_wheel.get_current_speed():.2f}\n"
        return health_check_text

    def sun_sensor_calibration_measurement(self, readings_queue):
        #TODO: handle sensor not available
        #if not sensor.is_available():
            #return f"Sun Sensor {sensor.id} not available for calibration."

        readings = {sensor.id: {} for sensor in self.sun_sensors}

        while self.calibrating_orientation_system:
            for sensor in self.sun_sensors:
                data = sensor.get_data()
                if data is None:
                    return "Calibration failed, sensor not found."

                yaw = (self.imu.get_current_yaw() + 90 * int(sensor.id)) % 360
                
                readings[sensor.id][yaw] = data

        # Compute average value for each yaw across all sensors
        average_readings = {}
        for sensor_id, yaw_data in readings.items():
            for yaw, value in yaw_data.items():
                if yaw not in average_readings:
                    average_readings[yaw] = []
                average_readings[yaw].append(value)

        readings = np.zeros(360)

        # Calculate average for each yaw
        for yaw, values in average_readings.items():
            float_values = [float(val) for val in average_readings[yaw]]
            avg_value = sum(float_values) / len(float_values)
            readings[int(yaw)] = avg_value  # Ensure yaw is an integer index

        readings_queue.put(readings)