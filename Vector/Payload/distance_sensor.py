import time
import board
import adafruit_vl53l4cd

i2c = board.I2C()
vl53 = adafruit_vl53l4cd.VL53L4CD(i2c)

vl53.timing_budget = 200  # Adjust for range vs. speed
vl53.start_ranging()

try:
    while True:
        while not vl53.data_ready:
            pass
        vl53.clear_interrupt()
        
        distance = vl53.distance
        
        if distance == 0:
            print("No target detected!")
        elif distance >= 8190:
            print("Sensor saturated (too bright or reflective)")
        else:
            print(f"Distance: {distance} mm")
        
        time.sleep(0.1)
        
except KeyboardInterrupt:
    vl53.stop_ranging()