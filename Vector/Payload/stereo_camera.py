import cv2 as cv
from matplotlib import pyplot as plt
from Payload.camera import Camera
import time
import threading

class StereoCamera:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Implement singleton pattern to prevent multiple camera managers"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(StereoCamera, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, log_queue, telemetry_queue):
        # Prevent re-initialization if already initialized
        if hasattr(self, '_initialized'):
            return

        self.log_queue = log_queue
        self.telemetry_queue = telemetry_queue
        self.left_camera = None
        self.right_camera = None
        self.left_camera_available = False
        self.right_camera_available = False
        self.initialization_attempts = 0
        self.max_initialization_attempts = 3
        
        # Initialize cameras with proper timing and error handling
        self._initialize_cameras()
        self._initialized = True
    
    def _initialize_cameras(self):
        self._cleanup_cameras()
        time.sleep(2)            
        self._initialize_left_camera()
        self._initialize_right_camera()

    
    def _initialize_left_camera(self):
        """Initialize left camera with error handling"""
        try:
            self.log_queue.put(("Payload","Initialising left camera (index 0)..."))
            self.left_camera = Camera(camera_index=0)

            if self.left_camera.is_initialized:
                self.left_camera_available = True
                self.log_queue.put(("Payload", "Left camera (index 0) initialised successfully"))
                self.telemetry_queue.put(("Payload", "Left Camera", "OPERATIONAL", None))                
            else:
                self.left_camera = None
                self.log_queue.put(("Payload", "Left camera (index 0) initialisation failed"))
                self.telemetry_queue.put(("Payload", "Left Camera", "INOPERATIVE", None))                
        except Exception as e:
            self.left_camera_available = False
            self.left_camera = None
            self.log_queue.put(("Payload", f"Failed to initialise left camera (index 0): {e}"))
            self.telemetry_queue.put(("Payload", "Left Camera", "INOPERATIVE", None))
        finally:
            return self.left_camera_available
    
    def _initialize_right_camera(self):
        """Initialize right camera with error handling"""
        try:
            self.log_queue.put(("Payload", "Initialising right camera (index 1)..."))
            self.right_camera = Camera(camera_index=1)

            if self.right_camera.is_initialized:
                self.right_camera_available = True
                self.log_queue.put(("Payload","Right camera (index 1) initialised successfully"))
                self.telemetry_queue.put(("Payload", "Right Camera", "OPERATIONAL", None))                
            else:
                self.right_camera = None
                self.log_queue.put(("Payload", "Right camera (index 1) initialisation failed"))
                self.telemetry_queue.put(("Payload", "Right Camera", "INOPERATIVE", None))
        except Exception as e:
            self.right_camera_available = False
            self.right_camera = None
            self.log_queue.put(("Payload", f"Failed to initialise right camera (index 1): {e}"))
            self.telemetry_queue.put(("Payload", "Right Camera", "INOPERATIVE", None))
        finally:
            return self.right_camera_available
    
    def _cleanup_cameras(self):
        """Clean up camera resources"""
        if self.left_camera is not None:
            try:
                self.left_camera.stop()
            except Exception as e:
                self.log_queue.put(("Payload", f"Error stopping left camera: {e}"))
            finally:
                self.left_camera = None
                self.left_camera_available = False
                self.telemetry_queue.put(("Payload", "Left Camera", "INOPERATIVE", None))
        
        if self.right_camera is not None:
            try:
                self.right_camera.stop()
            except Exception as e:
                self.log_queue.put(("Payload", f"Error stopping right camera: {e}"))
            finally:
                self.right_camera = None
                self.right_camera_available = False
                self.telemetry_queue.put(("Payload", "Right Camera", "INOPERATIVE", None))
    
    def is_stereo_available(self):
        """Check if both cameras are available for stereo processing"""
        return self.left_camera_available and self.right_camera_available
    
    def is_left_camera_available(self):
        """Check if left camera is available"""
        return self.left_camera_available
    
    def is_right_camera_available(self):
        """Check if right camera is available"""
        return self.right_camera_available

    def get_left_image(self):
        """Get image from left camera with error handling"""
        if not self.left_camera_available:
            raise RuntimeError("Left camera is not available")
        
        try:
            img = self.left_camera.get_frame()
            # Rotate the image 90 degrees anticlockwise
            img = cv.rotate(img, cv.ROTATE_90_COUNTERCLOCKWISE)
            return img
        except Exception as e:
            self.log_queue.put(("Payload", f"Error getting left camera frame: {e}"))
            # Mark camera as unavailable if it fails
            self.left_camera_available = False
            self.telemetry_queue.put(("Payload", "Left Camera", "INOPERATIVE", None))
            raise RuntimeError(f"Failed to get left camera frame: {e}")

    def get_right_image(self):
        """Get image from right camera with error handling"""
        if not self.right_camera_available:
            raise RuntimeError("Right camera is not available")
        
        try:
            img = self.right_camera.get_frame()
            # Rotate the image 90 degrees clockwise
            img = cv.rotate(img, cv.ROTATE_90_CLOCKWISE)
            return img
        except Exception as e:
            self.log_queue.put(("Payload", f"Error getting right camera frame: {e}"))
            # Mark camera as unavailable if it fails
            self.right_camera_available = False
            self.telemetry_queue.put(("Payload", "Right Camera", "INOPERATIVE", None))
            raise RuntimeError(f"Failed to get right camera frame: {e}")
    
    def get_depth_map(self):
        """Calculate depth map from stereo images with error handling"""
        if not self.is_stereo_available():
            raise RuntimeError("Stereo depth calculation requires both cameras to be available")
        
        try:
            left_image = self.get_left_image()
            right_image = self.get_right_image()
            
            depth_map = self.calculate_depth_map(left_image, right_image)
            return depth_map
        except Exception as e:
            self.log_queue.put(("Payload", f"Error calculating depth map: {e}"))
            raise RuntimeError(f"Failed to calculate depth map: {e}")
    
    def calculate_depth_map(self, left_image, right_image):
        """Calculate depth map from left and right images"""
        try:
            imgL = cv.cvtColor(left_image, cv.COLOR_BGR2GRAY)
            imgR = cv.cvtColor(right_image, cv.COLOR_BGR2GRAY)
            stereo = cv.StereoBM.create(numDisparities=16, blockSize=15)
            disparity = stereo.compute(imgL, imgR)
            plt.imshow(disparity, 'gray')
            plt.show()

            return disparity
        except Exception as e:
            self.log_queue.put(("Payload", f"Error in depth map calculation: {e}"))
            raise RuntimeError(f"Failed to calculate depth map: {e}")

    def save_images(self, path, file_name):
        """Save images from available cameras with error handling"""
        images_saved = []
        
        # Try to save left image
        if self.left_camera_available:
            try:
                left_image = self.get_left_image()
                left_path = f"{path}{file_name}_left.jpg"
                cv.imwrite(left_path, left_image)
                images_saved.append(left_path)
                self.log_queue.put(("Payload", f"Left image saved at {left_path}"))
            except Exception as e:
                self.log_queue.put(("Payload", f"Failed to save left image: {e}"))
        else:
            self.log_queue.put(("Payload", "Left camera not available - skipping left image"))
        
        # Try to save right image
        if self.right_camera_available:
            try:
                right_image = self.get_right_image()
                right_path = f"{path}{file_name}_right.jpg"
                cv.imwrite(right_path, right_image)
                images_saved.append(right_path)
                self.log_queue.put(("Payload", f"Right image saved at {right_path}"))
            except Exception as e:
                self.log_queue.put(("Payload", f"Failed to save right image: {e}"))
        else:
            self.log_queue.put(("Payload", "Right camera not available - skipping right image"))
        
        if not images_saved:
            raise RuntimeError("No images could be saved - no cameras available")
        
        return images_saved
    
    def get_available_image(self):
        """Get an image from any available camera (fallback method)"""
        if self.left_camera_available:
            try:
                return self.get_left_image(), "left"
            except Exception as e:
                self.log_queue.put(("Payload", f"Failed to get left image: {e}"))
        
        if self.right_camera_available:
            try:
                return self.get_right_image(), "right"
            except Exception as e:
                self.log_queue.put(("Payload", f"Failed to get right image: {e}"))
        
        raise RuntimeError("No cameras available or all cameras failed")
    
    def get_camera_status(self):
        """Get status information about both cameras"""
        return {
            "left_camera_available": self.left_camera_available,
            "right_camera_available": self.right_camera_available,
            "stereo_available": self.is_stereo_available(),
            "total_cameras": sum([self.left_camera_available, self.right_camera_available])
        }