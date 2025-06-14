import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
 
# imgL = cv.imread('tsukuba_l.png', cv.IMREAD_GRAYSCALE)
# imgR = cv.imread('tsukuba_r.png', cv.IMREAD_GRAYSCALE)
 
# stereo = cv.StereoBM.create(numDisparities=16, blockSize=15)
# disparity = stereo.compute(imgL,imgR)
# plt.imshow(disparity,'gray')
# plt.show()

class StereoCamera:
    def __init__(self, left_camera, right_camera):
        self.left_camera = left_camera
        self.right_camera = right_camera

    def get_left_image(self):
        return self.left_camera.get_image()

    def get_right_image(self):
        return self.right_camera.get_image()

    def get_stereo_images(self):
        return self.get_left_image(), self.get_right_image()
    
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

        return disparity