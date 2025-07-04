from ADCS.imu import Imu
from ADCS.reaction_wheel import ReactionWheel
from ADCS.sun_sensor import SunSensor
import time
import threading
import queue
import numpy as np

from ADCS.brushed_motor import BrushedMotor

class AdcsController:
    def __init__(self, log_queue):
        self.state = "INITIALIZING"
        self.log_queue = log_queue
        self.initialize_sun_sensors()
        self.initialize_orientation_system()
        self.calibrating_orientation_system = False
        self.state = "READY"
        self.target_yaw = None

    def get_state(self):
        return self.state

    def log(self, msg):
        self.log_queue.put(("ADCS", msg))

    def initialize_orientation_system(self):
        self.imu = Imu()
        #self.main_reaction_wheel = ReactionWheel(self.imu, motor_type="brushless")
        self.backup_reaction_wheel = ReactionWheel(self.imu, motor_type="brushed")
        self.current_reaction_wheel = self.backup_reaction_wheel
        #self.current_reaction_wheel = self.main_reaction_wheel
        #self.calibrate_orientation_system()

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
            gyroscope_text = f"X: {gyroscope_data[0]} °/s, Y: {gyroscope_data[1]} °/s, Z: {gyroscope_data[2]} °/s"

        if not orientation_data:
            orientation_text = "No data available"
            errors.append("Orientation data not available")
        else:
            orientation_text = f"X: {orientation_data[0]:.2f} °, Y: {orientation_data[1]:.2f} °, Z: {orientation_data[2]:.2f} °"

        health_check_text += f"Gyroscope: {gyroscope_text}\n"
        health_check_text += f"Orientation: {orientation_text}\n"

        if errors == []:
            is_component_ready = True

        return health_check_text, is_component_ready, errors

    def get_eps_health_check(self):
        voltage, current, temp = self.imu.get_bms_data()
        health_check_text = ""
        if voltage is None:
            health_check_text += f"Battery Voltage: NOT AVAILABLE\n"
            self.log("Battery voltage not available.\n")
        else:
            health_check_text += f"Battery Voltage: {voltage:.2f} V\n"

        if current is None:
            health_check_text += f"Battery Current: NOT AVAILABLE\n"
            self.log("Battery current not available.\n")
        else:
            health_check_text += f"Battery Current: {current:.2f} A\n"
        
        if temp is None:
            health_check_text += f"Battery Temperature: NOT AVAILABLE\n"
            self.log("Battery temperature not available.\n")
        else:
            if temp > 75:
                health_check_text += f"Battery Temperature: {temp:.2f} °C (CRITICAL)\n"
                self.log("Battery temperature is critical!")
            elif temp > 65:
                health_check_text += f"Battery Temperature: {temp:.2f} °C (WARNING)\n"
                self.log("Battery temperature is high.")
            else:
                health_check_text += f"Battery Temperature: {temp:.2f} °C (NOMINAL)\n"
        return health_check_text

    def calibrate_orientation_system(self):
        imu_status = self.imu.get_status()
        if imu_status["status"] == "ACTIVE" and self.current_reaction_wheel is not None:
            self.log("IMU initialized successfully.")
            self.calibrating_orientation_system = True
            self.log("Starting orientation system calibration...")

            #calibration_rotation_thread = threading.Thread(target=self.current_reaction_wheel.calibration_rotation)
            #calibration_rotation_thread.start()
            result = self.imu.calibrate()
            #result = self.imu.calibrate()
            #calibration_rotation_thread.join()

            if result:
                self.calibrate_sun_sensors()
            else:
                self.log("Orientation system calibration failed: IMU did not respond.")
        else:
            self.log(f"Orientation system calibration failed: Errors: {imu_status['errors']}")

    def initialize_sun_sensors(self):
        # Initialize the four sun sensors
        self.sun_sensors = [
            SunSensor(id=2, i2c_address=0x23, bus=1),
            SunSensor(id=1, i2c_address=0x23, bus=3),
            SunSensor(id=3, i2c_address=0x5c, bus=1),
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

    def get_current_yaw(self):
        # Get the current yaw from the IMU
        return self.imu.get_current_yaw()
    
    def get_reaction_wheel_health_check(self):
        # Get the status of the reaction wheel
        #health_check_text = f"Main Reaction Wheel RPM: {self.main_reaction_wheel.get_current_speed():.2f}\n"
        health_check_text += f"Backup Reaction Wheel RPM: {self.backup_reaction_wheel.get_current_speed():.2f}\n"
        return health_check_text

    def old_calibrate_sun_sensors(self):
        readings_queue = queue.Queue()

        if not self.calibrating_orientation_system:
            self.calibrating_orientation_system = True
        sun_sensor_measurement_thread = threading.Thread(target=self.sun_sensor_calibration_measurement, args=(readings_queue,))
        sun_sensor_measurement_thread.start()
        self.current_reaction_wheel.calibration_rotation()
        self.calibrating_orientation_system = False
        sun_sensor_measurement_thread.join()
    
        readings = readings_queue.get()

        if readings is not None and len(readings) > 0:
            max_index = np.argmax(readings)
            max_value = readings[max_index]
            self.log(f"ORIENTATION SYSTEM CALIBRATION COMPLETE with offset: {max_index}°")
            self.imu.set_calibration_offset(max_index)
        else:
            self.log("No sun sensor readings available to determine offset.")

    def calibrate_sun_sensors(self):
        readings_queue = queue.Queue()

        if not self.calibrating_orientation_system:
            self.calibrating_orientation_system = True
        sun_sensor_measurement_thread = threading.Thread(target=self.sun_sensor_calibration_measurement, args=(readings_queue,))
        sun_sensor_measurement_thread.start()
        self.current_reaction_wheel.calibration_rotation()
        self.calibrating_orientation_system = False
        sun_sensor_measurement_thread.join()

        offset = readings_queue.get()
    
        self.log(f"ORIENTATION SYSTEM CALIBRATION COMPLETE with offset: {offset}°")
        self.imu.set_calibration_offset(offset)

    def sun_sensor_calibration_measurement(self, readings_queue):
        readings = []

        # Collect readings while calibration is active
        while self.calibrating_orientation_system:
            total_irradiance = 0
            valid_sensors = 0
            for sensor in self.sun_sensors:
                data = sensor.get_data()
                if data is not None:
                    total_irradiance += data
                    valid_sensors += 1
            if valid_sensors > 0:
                avg_irradiance = total_irradiance / valid_sensors
                current_yaw = self.imu.get_current_yaw()
                readings.append((avg_irradiance, current_yaw))
            time.sleep(0.05)  # Avoid busy loop

        # Find the yaw with the maximum average irradiance
        if readings:
            max_reading = max(readings, key=lambda x: x[0])
            offset_yaw = max_reading[1]
        else:
            offset_yaw = 0  # Default if no readings

        readings_queue.put(offset_yaw)

        #     def sun_sensor_calibration_measurement(self, readings_queue):
        # readings = []

        # while self.calibrating_orientation_system:
        #     sum = 0
        #     for sensor in self.sun_sensors:
        #         sum += sensor.get_data()
        #     readings.append((sum, self.imu.get_current_yaw()))

        # offset = 0
        # yaw = 0

        # for reading in readings:
        #     if reading[0] > offset:
        #         offset = reading[0]
        #         yaw = reading[1]
        
        # readings_queue.put(offset)

    def old_sun_sensor_calibration_measurement(self, readings_queue):
        #TODO: handle sensor not available
        #if not sensor.is_available():
            #return f"Sun Sensor {sensor.id} not available for calibration."

        readings = {sensor.id: {} for sensor in self.sun_sensors}

        while self.calibrating_orientation_system:
            for sensor in self.sun_sensors:
                if not sensor.get_status()["status"] == "ACTIVE":
                    continue
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

    def test_reaction_wheel(self, kp, ki, kd, t=60, degree=0):
        rotation_thread = threading.Thread(target=self.current_reaction_wheel.activate_wheel_brushed, args=(degree, kp, ki, kd, 10, 10, False))
        rotation_thread.start()
        time.sleep(t)
        print("Stopping reaction wheel after test duration")
        self.stop_reaction_wheel()

        rotation_thread.join()
        self.current_reaction_wheel.stop_event.clear()

    def phase2_rotate(self, pipe):
        self.log("ADCS phase 2 rotation started")
        initial_yaw = self.imu.get_current_yaw()
        target_yaw = initial_yaw - 160
        pictures_taken = 0
        timeout = 600
        start_time = time.time()
        while pictures_taken <= 18: #or not self.current_reaction_wheel.stop_event.is_set()): #and (time.time() - start_time < timeout):
            self.current_reaction_wheel.activate_wheel_brushed(target_yaw) 
            yaw = self.imu.get_current_yaw()
            pipe.send(("take_picture", {"current_yaw": (abs(yaw % 360))}))
            last_yaw = abs(yaw)
            target_yaw += 20
            pictures_taken += 1
        self.stop_reaction_wheel()

    def phase2_sequence_rotation(self, pipe, sequence, targets):
        degree_distances = [0]

        degree_distances.extend([abs(targets[sequence[i]] - targets[sequence[i-1]]) % 360 for i in range(1, len(sequence))])

        current_target = None
        current_target_yaw = None
        
        for i in range(len(sequence)):
            current_target = sequence[i]
            current_target_yaw = targets.get(current_target, None)
            if current_target_yaw is None:
                self.log(f"Target {current_target} not found in numbers mapping.")
                continue
            self.current_reaction_wheel.activate_wheel_brushed(current_target_yaw, break_on_target=False)
            self.log(f"Rotated to target {current_target} with yaw {current_target_yaw}")
            pipe.send(("take_distance", None))  # send to Payload to measure distance
            pipe.send(("take_picture_rotation", None))  # send to Payload to measure distance
        
        return degree_distances

    
    def phase3_search_target(self, pipe):
        # Start rotating at specific speed
        # if apriltag is detected, stop rotating and record pose of target
        # if not, continue rotating until a timeout is reached
        current_yaw = self.get_current_yaw()
        rotation_thread = threading.Thread(target=self.current_reaction_wheel.activate_wheel_brushed, args=(current_yaw - 360,))
        rotation_thread.start()

        target_found = False
        timeout = 30  # seconds
        start_time = time.time()
        while (time.time() - start_time < timeout) and self.is_reaction_wheel_rotating():
            pipe.send(("detect_apriltag", None))
            line, args = pipe.recv()
            if line == "apriltag_detected":
                last_speed = self.current_reaction_wheel.get_current_speed()
                target_found = True
                break
 
        self.stop_reaction_wheel()
        
        rotation_thread.join()

        if target_found:
            pipe.send(("target_found", {"last_speed": last_speed}))
        else:
            self.log("Target not found within timeout period")
            pipe.send(("timeout", None))


    def phase3_reacquire_target(self, pipe):
        # get current target yaw
        current_yaw = self.get_current_yaw()
        # rotate until current yaw matches target yaw
        if self.target_yaw is not None:
            rotation_thread = threading.Thread(target=self.current_reaction_wheel.activate_wheel, args=(self.target_yaw,))
            rotation_thread.start()
        
            target_found = False
            time.sleep(5)  # wait for the wheel to start rotating
            initial_time = time.time()
            timeout = 10  # seconds
            while not target_found and (time.time() - initial_time < timeout) and self.is_reaction_wheel_rotating():
                pipe.send(("detect_apriltag", None))
                line, args = pipe.recv()
                if line == "apriltag_detected":
                    last_speed = self.current_reaction_wheel.get_current_speed(return_percentage=True)
                    target_found = True
                    break
            self.stop_reaction_wheel()

            rotation_thread.join()

            if target_found:
                self.phase3_align_target(pipe, last_speed)
            if not target_found:
                self.log("Target not reacquired within timeout period. Initiating search.")
                self.phase3_search_target()

        else:
            self.log("No target found yet. Initiating search.")
            self.phase3_search_target()

    def phase3_align_target(self, pipe, last_speed=0, break_on_target_aligned=True):
        # Rotate according to april tag rotation until the satellite is aligned with the target
        self.log("Aligning with target...")
        rotation_thread = threading.Thread(target=self.current_reaction_wheel.activate_wheel_brushed_to_align, args=(last_speed,))
        rotation_thread.start()

        self.log("Alignment complete.")
        
        target_found = True

        while target_found is True and self.is_reaction_wheel_rotating():
            pipe.send(("detect_apriltag", None))
            line, args = pipe.recv()
            if line == "apriltag_detected":
                target_pose = args.get("pose", None)
                if target_pose is None:
                    self.log("April Tag lost")
                    target_found = False
                x, y, z = target_pose['translation']
                pitch,yaw,roll = target_pose['degree']
                self.current_reaction_wheel.desired_aligment = yaw
                if abs(yaw) < 2:  # Tolerance of 2
                    if self.target_yaw != self.get_current_yaw():
                        self.log(f"Aligned with target at yaw: {self.target_yaw} degrees")
                    self.target_yaw = self.get_current_yaw()
                    self.log(f"Aligned with target at yaw: {self.target_yaw} degrees")
                    if break_on_target_aligned:
                        self.log("Target aligned successfully. Stopping rotation.")
                        pipe.send(("target_aligned", {"yaw": self.target_yaw}))
                        break

        rotation_thread.join()

        self.log("Target lost during alignment")
        pipe.send(("target_lost", None))

    def phase3b_read_target(self, pipe):
        # Lock target yaw and get any april tag pose
        rotation_thread = threading.Thread(target=self.current_reaction_wheel.activate_wheel, args=(self.target_yaw,))
        rotation_thread.start()

        while self.is_reaction_wheel_rotating():
            pipe.send(("detect_apriltag", None))
            line, args = pipe.recv()
            if line == "apriltag_detected":
                target_pose = args.get("pose", None)
                if target_pose is not None:
                    pitch, yaw, roll = target_pose['degree']
                    pipe.send(("reading_target", {"yaw": yaw, "pitch": pitch, "roll": roll}))
        

    def stop_reaction_wheel(self):
        self.current_reaction_wheel.set_state("STANDBY")
        if not self.current_reaction_wheel.stop_event.is_set():
            self.current_reaction_wheel.stop_event.set()
        self.current_reaction_wheel.stop_event.clear()

    def is_reaction_wheel_rotating(self):
        return self.current_reaction_wheel.get_state() == "ROTATING" or self.current_reaction_wheel.get_state() == "ALIGNING"


        