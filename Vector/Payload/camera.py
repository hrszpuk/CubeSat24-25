from picamera2 import Picamera2
from libcamera import controls
import cv2


class Camera:
    def __init__(self, camera_index=0, width=1920, height=1080, framerate=30):
        self.picam2 = Picamera2(camera_index)
        self.picam2.configure(self.picam2.create_preview_configuration(
            main={"size": (width, height)},
            lores={"size": (640, 480)},
            controls={
                "FrameDurationLimits": (1_000_000 // framerate, 1_000_000 // framerate),
                "ExposureTime": 0,
                "AnalogueGain": 1.0,
                "AwbMode": controls.AwbModeEnum.Auto,
                "AfMode": controls.AfModeEnum.Continuous
            }
        ))
        self.picam2.start()

    def get_frame(self):
        return self.picam2.capture_array()

    def show_frame(self):
        frame = self.get_frame()
        cv2.imshow("Camera Feed", frame)
        cv2.waitKey(1000)