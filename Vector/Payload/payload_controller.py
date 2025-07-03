import os
import glob
from Payload.distance_sensor import DistanceSensor
from Payload.stereo_camera import StereoCamera
from Payload.number_identifier import identify_numbers_from_files
from Payload import tag_finder

class PayloadController:
    def __init__(self, log_queue, telemetry_queue):
        self.state = "INITIALISING"
        self.log_queue = log_queue
        self.telemetry_queue = telemetry_queue
        self.stereo_camera = StereoCamera(self.log_queue, telemetry_queue)
        self.distance_sensor = DistanceSensor(self.log_queue, telemetry_queue)
        self.state = "READY"
        self.numbers_identified = []

    def get_camera_status(self):
        return self.stereo_camera.get_camera_status()

    def get_state(self):
        return self.state

    def health_check(self):
        health_check_text = ""
        errors = []

        # get the status of the stereo camera
        sc_health_check_text, sc_health_check, sc_errors = self.get_stereo_camera_health_check()
        health_check_text += sc_health_check_text
        errors.extend(sc_errors)

        # get the status of the distance sensor
        ds_health_check_text, ds_health_check, ds_errors = self.get_distance_sensor_health_check()
        health_check_text += ds_health_check_text
        errors.extend(ds_errors)

        # check subsystem health
        if ds_health_check and sc_health_check:
            self.status = "OK"
            health_check_text += "STATUS: OK"
        else:
            self.status = "DOWN"
            health_check_text += "STATUS: DOWN - Error in one or more components"

        return health_check_text, errors

    def get_stereo_camera_health_check(self):
        health_check_text = ""
        is_component_ready = False
        errors = []

        status = self.stereo_camera.get_camera_status()

        if status["left_camera_available"] is False:
            health_check_text += "Left camera: INACTIVE\n"
            errors.append("Left camera not available")
        else:
            health_check_text += "Left camera: ACTIVE\n"
        if status["right_camera_available"] is False:
            health_check_text += "Right camera: INACTIVE\n"
            errors.append("Right camera not available")
        else:
            health_check_text += "Right camera: ACTIVE\n"
        
        if errors:
            health_check_text += "Stereo Camera: DOWN\n"
        else:
            is_component_ready = True

        return health_check_text, is_component_ready, errors
    

    def get_distance_sensor_health_check(self):
        health_check_text = ""
        is_component_ready = False
        errors = []

        if self.distance_sensor.get_distance() is None:
            errors.append("Distance sensor data not available")
            health_check_text += f"Distance Sensor: INACTIVE\n"
        else:
            health_check_text += f"Distance Sensor: ACTIVE\n"
            is_component_ready = True

        return health_check_text, is_component_ready, errors

    def identify_numbers_from_files(self):
        image_paths = glob.glob("images/phase2/*.jpg")
        self.numbers_identified = identify_numbers_from_files(image_paths)
        print(f"Identified numbers: {self.numbers_identified}")
        return self.numbers_identified

    def take_picture(self, directory, filename):
        os.makedirs(directory, exist_ok=True)
        self.stereo_camera.take_picture(directory, filename)
    
    def take_picture_phase_2(self, yaw):
        # Get the current working directory
        current_path = os.getcwd()
        directory = "images/phase2/"
        os.makedirs(directory, exist_ok=True)
        # NOTE(remy): added support for passing "yaw" as a string for manual mode
        self.stereo_camera.save_images("images/phase2/", round(yaw))
        self.log_queue.put(("Payload", f"Image taken and saved in {current_path}/{directory}"))

    def take_picture_phase_3(self):
        # Get the current working directory
        current_path = os.getcwd()
        directory = "images/phase3/"
        os.makedirs(directory, exist_ok=True)
        self.stereo_camera.save_images("images/phase3/", "damage_assessment")
        self.log_queue.put(("Payload", f"Image taken and saved in {current_path}/{directory}"))

        return 

    def take_distance(self):
        return self.distance_sensor.get_distance()

    def detect_apriltag(self):
        tagfinder_obj = tag_finder.Detector(0.049)
        tagfinder_obj.capture_Camera()
        if not tagfinder_obj.getPose(): 
            return None
        
        pose = tagfinder_obj.Poses[-1]
        return pose