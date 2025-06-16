from Vector.Payload.distance_sensor import DistanceSensor
from Vector.Payload.stereo_camera import StereoCamera

class PayloadController:
    def __init__(self):
        self.stereo_camera = StereoCamera()
        self.distance_sensor = DistanceSensor()

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

        if not left_image:
            errors.append("Left camera not available")
        if not right_image:
            errors.append("Right camera not available")
        else:
            health_check_text += f"Stereo Camera: OPERATIONAL"
            is_component_ready = True

        return health_check_text, is_component_ready, errors
    

    def get_distance_sensor_health_check(self):
        health_check_text = ""
        is_component_ready = False
        errors = []

        distance_data = self.distance_sensor.get_data()
        if not distance_data:
            errors.append("Distance sensor data not available")
        else:
            health_check_text += f"Distance Sensor: {distance_data} cm"
            is_component_ready = True

        return health_check_text, is_component_ready, errors