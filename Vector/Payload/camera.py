from picamera2 import Picamera2
from libcamera import controls
import cv2
import os
import numpy as np

class Camera:
    def __init__(self, camera_index=0, width=1920, height=1080, framerate=30):
        self.camera_index = camera_index
        self.is_initialized = False
        
        try:
            self.picam2 = Picamera2(camera_index)
            
            # Create configuration
            config = self.picam2.create_preview_configuration(
                main={"size": (width, height)},
                lores={"size": (640, 480)},
                controls={
                    "FrameDurationLimits": (1_000_000 // framerate, 1_000_000 // framerate),
                    "ExposureTime": 0,
                    "AnalogueGain": 1.0,
                    "AwbMode": controls.AwbModeEnum.Auto,
                    "AfMode": controls.AfModeEnum.Continuous
                }
            )
            
            # Configure the camera
            self.picam2.configure(config)
            
            # Start the camera
            self.picam2.start()
            self.is_initialized = True
            
        except Exception as e:
            print(f"Failed to initialize camera {camera_index}: {e}")
            self.picam2 = None
            return
        
        # Load calibration data only if camera initialized successfully
        if self.is_initialized:
            if camera_index == 0:
                calib_path = '/home/vector/CubeSat24-25/Vector/Payload/camera_calibrations/calibration_savez_left.npz'
            else:
                calib_path = '/home/vector/CubeSat24-25/Vector/Payload/camera_calibrations/calibration_savez_right.npz'
            
            if not os.path.exists(calib_path):
                print(f"Warning: Calibration file not found: {calib_path}")
                self.distortion = None
                self.camera_params = None
                self.matrix = None
                return
                
            try:
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
            except Exception as e:
                print(f"Error loading calibration data: {e}")
                self.distortion = None
                self.camera_params = None
                self.matrix = None

    def get_frame(self):
        if not self.is_initialized or self.picam2 is None:
            return None
        try:
            return self.picam2.capture_array()
        except Exception as e:
            print(f"Error capturing frame from camera {self.camera_index}: {e}")
            return None

    def show_frame(self):
        frame = self.get_frame()
        if frame is not None:
            cv2.imshow("Camera Feed", frame)
            cv2.waitKey(1000)
        else:
            print(f"Cannot show frame - camera {self.camera_index} not available")
    
    def stop(self):
        """Stop the camera and clean up resources"""
        if self.is_initialized and self.picam2 is not None:
            try:
                self.picam2.stop()
                self.picam2.close()
            except Exception as e:
                print(f"Error stopping camera {self.camera_index}: {e}")
            finally:
                self.is_initialized = False
                self.picam2 = None
    
    def __del__(self):
        """Destructor to ensure camera resources are cleaned up"""
        self.stop()