import glob
from Payload.distance_sensor import DistanceSensor
from Payload.stereo_camera import StereoCamera
from Payload.number_identifier import get_numbers, find_number_orientation

class PayloadController:
    def __init__(self, log_queue):
        self.state = "INITIALIZING"
        self.log_queue = log_queue
        self.stereo_camera = StereoCamera()
        self.distance_sensor = DistanceSensor()
        self.state = "READY"

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
        if sc_health_check and ds_health_check:
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

        left_image = self.stereo_camera.get_left_image()
        right_image = self.stereo_camera.get_right_image()

        if left_image is None:
            errors.append("Left camera not available")
        if right_image is None:
            errors.append("Right camera not available")
        
        if errors:
            health_check_text += "Stereo Camera: DOWN\n"
        else:
            health_check_text += f"Stereo Camera: ACTIVE\n"
            is_component_ready = True

        return health_check_text, is_component_ready, errors
    

    def get_distance_sensor_health_check(self):
        health_check_text = ""
        is_component_ready = False
        errors = []

        if self.distance_sensor is None:
            errors.append("Distance sensor data not available")
            health_check_text += f"Distance Sensor: DOWN\n"
        else:
            health_check_text += f"Distance Sensor: ACTIVE\n"
            is_component_ready = True

        return health_check_text, is_component_ready, errors

    def identify_numbers_from_files(self):
        image_paths = glob.glob("images/numbers/*.jpeg")  # Adjust the number of images as needed
        for image_path in sorted(image_paths):
            numbers = (get_numbers(image_path))
            find_number_orientation(image_path, numbers)