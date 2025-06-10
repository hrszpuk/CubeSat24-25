import serial
import math

class Imu:
    def __init__(self):
        #self.serial_connection = serial.Serial('/dev/serial0', baudrate=115200, timeout=1)
        self.serial_connection = serial.Serial('/dev/ttyACM0', baudrate=115200, timeout=1)
        self.start_imu()

    def get_serial_text(self):
        line = self.serial_connection.readline().decode('utf-8').strip()
        if line:
            return line
        #else:
            #raise ValueError("Received empty data from IMU")
        
    def get_status(self):
        try:
            self.start_imu()
            return {"status": "ACTIVE", "errors": []}
        except serial.SerialException as e:
            error = f"IMU initialization failed: {e}"
            return {"status": "INACTIVE", "errors": [error]}
    
    # Get IMU data from the serial connection and parse it
    def get_imu_data(self):
        try: 
            line = self.get_serial_text()
            gyroscope_data, orientation_data = self.parse_imu_data(line)
            return {"gyroscope": gyroscope_data, "orientation": orientation_data, "errors": []}
        except Exception as e:
            error = ((f"Failed to read from IMU: {e}"))
            return {"gyroscope": None, "orientation": None, "error": error}

    def start_imu(self):
        if not self.serial_connection.is_open:
            self.serial_connection.open()

    def send_command(self, command):
        if not self.serial_connection.is_open:
            raise serial.SerialException("Serial connection is not open.")
        #self.serial_connection.write(command.encode('utf-8') + b'\r')
        #print(f"Command sent: {command}")
        self.serial_connection.write(b'CALIBRATE\r')

    def parse_imu_data(self, line):
        # Example line: "Gyroscope: 0.2 0.5 0.02 | Orientation: 0.2 0.5 0.02"
        try:
            # Split the string by the pipe symbol and extract relevant parts
            parts = line.split('|')
            gyroscope_data = parts[0].split(':')[1].strip().split()
            orientation_data = parts[1].split(':')[1].strip().split()

            # Convert the string numbers to floats
            gyroscope = [round(math.degrees(float(num)), 2) for num in gyroscope_data]
            orientation = [round(math.degrees(float(num)), 2) for num in orientation_data]

            return gyroscope, orientation
        except (IndexError, ValueError) as e:
            raise ValueError(f"Failed to parse IMU data: {e}")