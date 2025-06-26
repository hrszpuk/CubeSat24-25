from stereo_camera import StereoCamera
import apriltag
import cv2, math, json
import numpy as np
import dt_apriltags as dt_april
import apriltag
from transforms3d.euler import mat2euler

# Code adapted from: https://github.com/suriono/apriltag

class Detector:
   def __init__(self, tag_size, camera_obj=StereoCamera()):
      self.tag_size = tag_size
      self.camera_obj = camera_obj
      options = apriltag.DetectorOptions(families="tag25h9") 
      self.detector = apriltag.Detector(options)
      self.dt_detector = dt_april.Detector(searchpath=['apriltags'],
                       families='tag25h9',
                       nthreads=1,
                       quad_decimate=1.0,
                       quad_sigma=0.0,
                       refine_edges=1,
                       decode_sharpening=0.25,
                       debug=0)
      self.img = self.camera_obj.get_left_image()
      self.camera_width,self.camera_height = self.img.shape[1],self.img.shape[0]

   def capture_Camera(self):
      self.img = self.camera_obj.get_left_image()

   def getPose(self):
      self.gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)

      self.dt_results = self.dt_detector.detect(self.gray,True,self.camera_obj.left_camera.camera_params, self.tag_size)


      self.Yaw, self.Pitch, self.Roll, self.Translation = [], [], [], []
      self.Poses = []

      for result in self.dt_results:
         pose = {}
         radian, degree = self.get_Euler(result.pose_R)

         X, Y, Z = result.pose_t * 1000.0 # Convert to mm if result.pose_t is in meters

         position = (X[0], Y[0], Z[0])

         pose['translation'] = position
         pose['degree'] = degree
         pose['radian'] = radian
         pose['tag_family'] = result.tag_family.decode("utf-8")
         pose['tag_id'] = result.tag_id

         self.Poses.append(pose)

      return (len(self.dt_results) > 0)

   def getCamera_Pose(self, result):
      self.pose, e0, e1 = self.detector.detection_pose(result, self.camera_obj.left_camera.camera_params)
      np_pose = np.array(self.pose)
      # Find where the camera is if the tag is at the origin
      camera_pose = np.linalg.inv(self.pose)
      camera_pose[0][3] *= self.tag_size * 1000
      camera_pose[1][3] *= self.tag_size * 1000
      camera_pose[2][3] *= self.tag_size * 1000
      self.camera_X = camera_pose[0][3]
      self.camera_Y = camera_pose[1][3] 
      self.camera_Z = camera_pose[2][3] 

   def get_Euler(self, Rmatrix):
      radian = np.array(mat2euler(Rmatrix[0:3][0:3], 'sxyz')) 
      degree = np.array(np.rad2deg(mat2euler(Rmatrix[0:3][0:3], 'sxyz'))) 
      return radian, degree

   def get_All_Tag_Info(self):
      X,Y,Z = self.X, self.Y, self.Z
      yaw,pitch,roll = self.Yaw[0],self.Pitch[0],self.Roll[0]
      return self.tag_family, self.tag_id, X,Y,Z, yaw,pitch,roll