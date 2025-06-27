import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
from Payload.camera import Camera

class StereoCamera:
    def __init__(self):
        self.left_camera = Camera(camera_index=0)
        self.right_camera = Camera(camera_index=1)

    def get_left_image(self):
        return self.left_camera.get_frame()

    def get_right_image(self):
        return self.right_camera.get_frame()
    
    def get_depth_map(self):
        left_image = self.get_left_image()
        right_image = self.get_right_image()
        
        depth_map = self.calculate_depth_map(left_image, right_image)
        
        return depth_map
    
    def calculate_depth_map(self, left_image, right_image):
        imgL = cv.cvtColor(left_image, cv.COLOR_BGR2GRAY)
        imgR = cv.cvtColor(right_image, cv.COLOR_BGR2GRAY)

        stereo = cv.StereoBM.create(numDisparities=16, blockSize=15)
        disparity = stereo.compute(imgL,imgR)

        plt.imshow(disparity,'gray')
        plt.show()

        return disparity

    def save_images(self, path, file_name):
        left_image = self.get_left_image()
        right_image = self.get_right_image()

        cv.imwrite(f"{path}{file_name}_left.jpg", left_image)
        cv.imwrite(f"{path}{file_name}_right.jpg", right_image)
        print(f"Images saved at {path}{file_name}_left.jpg and {path}{file_name}_right.jpg")