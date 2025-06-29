import sys, time
import tag_finder as tag_finder
import tag.location as location
import tag.drawing as drawing

# Code adapted from: https://github.com/suriono/apriltag

def run(tagfinder_obj):
   tagfinder_obj.capture_Camera()
   if not tagfinder_obj.getPose(): 
      print("===== No tag found")
      return 0

   for index, pose in enumerate(tagfinder_obj.Poses):
      (X,Y,Z) = pose['translation']
      (pitch,yaw,roll) = pose['degree']
      print("Tag: family=", pose['tag_family'], " , ID=" , pose['tag_id'])
      print(" ==== X=" , int(X),",Y=",int(Y),", Z=",int(Z))
      print(" ==== Yaw=", int(yaw),", Pitch=",int(pitch),", Roll=",int(roll))


tagfinder_obj = tag_finder.Detector(0.049)
while True:
   run(tagfinder_obj)