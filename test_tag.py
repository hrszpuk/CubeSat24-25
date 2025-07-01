import numpy as np
import cv2
#from stereo_camera import StereoCamera
from dt_apriltags import Detector

# camera = StereoCamera()
# img = camera.get_left_image()
# cv2.imwrite('test_image.png', img)  # Save the image for debugging

img = cv2.imread('test_image1.png')

if len(img.shape) == 3:
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
else:
    gray_img = img

# --- Ensure the image is C-contiguous and of type uint8 ---
# This is a common cause of segfaults with C extensions
if not gray_img.flags['C_CONTIGUOUS']:
    gray_img = np.ascontiguousarray(gray_img)
gray_img = gray_img.astype(np.uint8) # Ensure data type is uint8

# Initialize the AprilTag detector
# You can specify multiple tag families to detect simultaneously
# Common families: tag16h5, tag25h9, tag36h10, tag36h11, tagStandard41h12
# For dt-apriltags, families should be a space-separated string
detector = Detector(searchpath=['apriltags'],
                       families='tag25h9',
                       nthreads=1,
                       quad_decimate=1.0,
                       quad_sigma=0.0,
                       refine_edges=1,
                       decode_sharpening=0.25,
                       debug=0)

# Detect tags in the image
results = detector.detect(gray_img) # Pass the grayscale image to the detector

# Print the detection results
if results:
    print(f"Found {len(results)} AprilTags:")
    for i, tag in enumerate(results):
        print(f"--- Tag {i+1} ---")
        print(f"Tag ID: {tag.tag_id}")
        print(f"Tag Family: {tag.tag_family}")  # Show which family was detected
        print(f"Center: {tag.center}")
        print(f"Corners: {tag.corners}")
        print(f"Homography: \n{tag.homography}")
        print(f"Decision Margin: {tag.decision_margin}")
else:
    print("No AprilTags detected.")