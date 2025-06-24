from picamera2 import Picamera2
from libcamera import controls
import cv2
import os
import numpy as np

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
        if camera_index == 0:
            calib_path = 'camera_calibrations/calibration_savez_left.npz'
        else:
            calib_path = 'camera_calibrations/calibration_savez_right.npz'
        if not os.path.exists(calib_path):
            raise FileNotFoundError(f"Calibration file not found: {calib_path}")
        with np.load(calib_path) as X:
            mtx, dist, self.rvecs, self.tvecs = [X[i] for i in ('mtx','distort','rvecs','tvecs')]

        fx   = mtx[0,0]
        fy   = mtx[1,1]
        cx   = mtx[0,2]
        cy   = mtx[1,2]

        self.distortion = dist[0]
        self.camera_params = (fx,fy,cx,cy)
        self.matrix = np.array([
            self.camera_params[0], 0, self.camera_params[2],
            0, self.camera_params[1], self.camera_params[3],
            0, 0, 1
            ]).reshape(3, 3)

    def get_frame(self):
        return self.picam2.capture_array()

    def show_frame(self):
        frame = self.get_frame()
        cv2.imshow("Camera Feed", frame)
        cv2.waitKey(1000)