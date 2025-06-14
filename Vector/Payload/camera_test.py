from picamera2 import Picamera2

picam2 = Picamera2()
picam2.start_preview()
picam2.start()
frame = picam2.capture_array()
print("Camera works! Image shape:", frame.shape)
picam2.stop()