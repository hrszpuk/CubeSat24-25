import time
import serial
import logging
from typing import Optional, Tuple, Dict, List

# Set up logging
#TODO
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Imu:
    def __init__(self, port: str = '/dev/serial0', baudrate: int = 9600, timeout: float = 1.0):
        self.serial_connection = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
            dsrdtr=False,  # Prevents Arduino auto-reset
            rtscts=False   # Disable hardware flow control
        )
        time.sleep(2)  # Wait for serial stabilization
        self._clear_buffers()

    def _clear_buffers(self) -> None:
        """Clear serial buffers to avoid stale data."""
        if self.serial_connection.is_open:
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()

    def get_serial_text(self, max_attempts: int = 3) -> Optional[str]:
        """Read a line from serial with retries."""
        for attempt in range(max_attempts):
            try:
                line = self.serial_connection.read_until(b'\n').decode('ascii', errors='ignore').strip()
                if line:  # Only return if data is valid
                    return line
            except (UnicodeDecodeError, serial.SerialException) as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(0.1)
        return None

    def get_status(self) -> Dict[str, str | List[str]]:
        """Check serial connection status."""
        try:
            return {
                "status": "ACTIVE" if self.serial_connection.is_open else "INACTIVE",
                "errors": []
            }
        except serial.SerialException as e:
            error = f"IMU connection error: {e}"
            logger.error(error)
            return {"status": "INACTIVE", "errors": [error]}

    def parse_imu_data(self, line: str) -> Tuple[List[float], List[float]]:
        """
        Parse IMU data with flexible formatting.
        Example line: "Gyroscope: 0.1 0.2 0.3 | Orientation: 10.0 -5.0 20.0"
        """
        gyroscope, orientation = [], []
        try:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            
            # Parse Gyroscope (if available)
            if len(parts) > 0 and ":" in parts[0]:
                gyro_str = parts[0].split(":")[1].strip()
                gyroscope = [float(x) for x in gyro_str.split()[:3]]  # Take first 3 values
            
            # Parse Orientation (if available)
            if len(parts) > 1 and ":" in parts[1]:
                orient_str = parts[1].split(":")[1].strip()
                orientation = [float(x) for x in orient_str.split()[:3]]  # Take first 3 values
            
            return gyroscope, orientation
        except (ValueError, IndexError, AttributeError) as e:
            logger.error(f"Failed to parse IMU data: {e}")
            return [], []  # Return empty lists on failure

    def get_imu_data(self, max_attempts: int = 3) -> Dict[str, Optional[List[float]] | List[str]]:
        """Fetch IMU data with error handling."""
        errors = []
        for attempt in range(max_attempts):
            line = self.get_serial_text()
            if not line:
                errors.append(f"Attempt {attempt + 1}: No data received")
                continue
            
            gyro, orient = self.parse_imu_data(line)
            if gyro or orient:  # At least one dataset is valid
                return {"gyroscope": gyro, "orientation": orient, "errors": errors}
            else:
                errors.append(f"Attempt {attempt + 1}: Invalid data format")
        
        return {"gyroscope": None, "orientation": None, "errors": errors}

    def get_orientation(self) -> List[float]:
        """Get orientation (convenience method)."""
        imu_data = self.get_imu_data()
        if imu_data["orientation"] is None:
            raise ValueError(f"No orientation data. Errors: {imu_data['errors']}")
        return imu_data["orientation"]

    def get_current_yaw(self):
        orientation_data= self.get_orientation()
        yaw = orientation_data[0]
        return yaw

    def send_command(self, command: str) -> None:
        """Send a command (e.g., 'CALIBRATE')."""
        if not self.serial_connection.is_open:
            raise serial.SerialException("Serial port not open")
        self.serial_connection.write(f"{command}\n".encode('utf-8'))
        self.serial_connection.flush()

    def calibrate(self) -> None:
        """Trigger calibration."""
        #TODO add error handling for IMU calibration
        print("Waiting for IMU calibration to complete...")
        self.send_command('CALIBRATE')
        time.sleep(0.3)
        while True:
            line = self.get_serial_text()
            if line:
                if "complete" in line:
                    break
                    print(line)
            else:
                print(".")
        print("IMU calibration completed successfully!")

# Example Usage
if __name__ == "__main__":
    imu = Imu()
    try:
        while True:
            data = imu.get_imu_data()
            print(f"Gyro: {data['gyroscope']}, Orient: {data['orientation']}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting...")