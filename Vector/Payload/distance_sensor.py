import time
import board
import adafruit_vl53l4cd

class DistanceSensor:
    def __init__(self, log_queue, telemetry_queue):
        try:
            self.log_queue = log_queue
            self.telemetry_queue = telemetry_queue
            i2c = board.I2C()
            self.sensor = adafruit_vl53l4cd.VL53L4CD(i2c)
            self.sensor.timing_budget = 200
            self.sensor.inter_measurement = 500
            self.sensor.start_ranging()
            self.telemetry_queue.put(("Payload", "Distance Sensor", "ACTIVE", None))
        except Exception as e:
            self.sensor = None
            self.log_queue.put(("Payload", f"Distance sensor failed to initialise: {e}"))
            self.telemetry_queue.put(("Payload", "Distance Sensor", "INACTIVE", None))

    def get_distance(self):
        if self.sensor is None:
            return None
        
        # Wait for data to be ready (with timeout)
        timeout = time.time() + 2.0  # 2 second timeout

        while not self.sensor.data_ready:
            if time.time() > timeout:
                self.log_queue.put(("Payload", "Timeout waiting for distance sensor data"))
                return None
            
            time.sleep(0.01)  # Small delay to avoid busy waiting
        
        self.sensor.clear_interrupt()
        distance = self.sensor.distance
        return distance