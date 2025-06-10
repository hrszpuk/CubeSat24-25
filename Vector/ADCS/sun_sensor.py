import os
import sys
import smbus

CMD_READ = 0x10 # Command to read data from the sensor

class SunSensor:
    """
    Class to interface with a Sun Sensor (BH1750) using I2C communication.
    """
    def __init__(self, id, i2c_address=0x23, bus=1):
        self.id = id
        self.i2c_address = i2c_address
        self.bus = smbus.SMBus(bus)

    def get_data(self):
        try:
            data = self.bus.read_i2c_block_data(self.i2c_address, CMD_READ)
            result = (data[1] + (256 * data[0])) / 1.2
            return format(result,'.0f')
        except OSError as error:
            if 121 == error.errno:
                print('No sensor found')
            else:
                print('Error:', sys.exc_info()[0])
    
    def get_status(self):
        try:
            self.get_data()
            return {"id": self.id, "status": "ACTIVE", "errors": []}
        except Exception as e:
            return {"id": self.id, "status": "INACTIVE", "errors": f"SunSensor {self.id} initialization failed. Error: {str(e)}"}