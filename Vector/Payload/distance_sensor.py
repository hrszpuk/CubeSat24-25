import time
import board
import adafruit_vl53l4cd

class DistanceSensor:
    def __init__(self):
        try:
            i2c = board.I2C()
            self.sensor = adafruit_vl53l4cd.VL53L4CD(i2c)
            self.sensor.timing_budget = 200
            self.sensor.inter_measurement = 500
            self.sensor.start_ranging()
        except Exception as e:
            print(f"ERROR: {e}") # SWAP for logging
            self.sensor = None

    def get_distance(self):
        if self.sensor is None:
            return None
        
        # Wait for data to be ready (with timeout)
        timeout = time.time() + 2.0  # 2 second timeout
        while not self.sensor.data_ready:
            if time.time() > timeout:
                print("Timeout waiting for sensor data")
                return None
            time.sleep(0.01)  # Small delay to avoid busy waiting
        
        self.sensor.clear_interrupt()
        distance = self.sensor.distance
        return distance
