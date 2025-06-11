import time
import serial

class Imu:
    def __init__(self):
        # Initialize with DTR=False to prevent Arduino reset
        self.serial_connection = serial.Serial(
            '/dev/ttyACM0',
            baudrate=9600,
            timeout=1,
            dsrdtr=False  # This prevents Arduino from resetting
        )
        time.sleep(2)  # Wait for the serial connection to initialize
        self._clear_buffers()

    def _clear_buffers(self):
        """Clear serial buffers without causing resets"""
        if self.serial_connection.is_open:
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()

    def get_serial_text(self):
        try:
            line = self.serial_connection.read_until(b'\n').decode('ascii', errors='ignore').strip()
            return line
        except UnicodeDecodeError:
            # Fallback to raw bytes if decoding fails
            return str(self.serial_connection.readline())  # Returns byte string representation
        
    def get_status(self):
        try:
            # Just check if connection is open, don't restart it
            return {
                "status": "ACTIVE" if self.serial_connection.is_open else "INACTIVE",
                "errors": []
            }
        except serial.SerialException as e:
            error = f"IMU connection error: {e}"
            return {"status": "INACTIVE", "errors": [error]}
    
    def get_imu_data(self):
        try: 
            line = self.get_serial_text()
            if not line:
                line = self.get_serial_text()
                if not line:
                    return {"gyroscope": None, "orientation": None, "errors": ["No data received"]}
                
            gyroscope_data, orientation_data = self.parse_imu_data(line)
            return {"gyroscope": gyroscope_data, "orientation": orientation_data, "errors": []}
        except Exception as e:
            return {"gyroscope": None, "orientation": None, "errors": [str(e)]}
    
    def get_orientation(self):
        imu_data = self.get_imu_data()
        print(imu_data) # Debugging line to see the raw IMU data
        if imu_data["orientation"] is not None:
            return imu_data["orientation"]
        else:
            raise ValueError("IMU data is not available or incomplete.")

    def send_command(self, command):
        if not self.serial_connection.is_open:
            raise serial.SerialException("Serial connection not open")
        
        self.serial_connection.write((command + '\n').encode('utf-8'))
        self.serial_connection.flush()

    def calibrate(self):
        self.send_command('CALIBRATE')

    def parse_imu_data(self, line):
        # Example line: "Gyroscope: 0.2 0.5 0.02 | Orientation: 0.2 0.5 0.02"
        try:
            parts = line.split('|')

            prints = [part.strip() for part in parts if part.strip()]
            
            if len(parts) < 2:
                raise ValueError("Invalid data format - missing parts")
            
            gyroscope = []
            orientation = []
            
            # Extract gyroscope data
            if ":" in parts[0]:
                gyroscope_data = parts[0].split(':')[1].strip().split()
                gyroscope = [round(float(num), 2) for num in gyroscope_data[:3]]
                if len(gyroscope) != 3:
                    raise ValueError("IMU data incomplete for gyroscope")
            
            # Extract orientation data
            if ":" in parts[1]:
                orientation_data = parts[1].split(':')[1].strip().split()
                orientation = [round(float(num), 2) for num in orientation_data[:3]]
                if len(orientation) != 3:
                    raise ValueError("IMU data incomplete for orientation")
            
            return gyroscope, orientation
        except (IndexError, ValueError) as e:
            raise ValueError(f"Failed to parse IMU data: {e}")