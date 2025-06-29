import math
import time
import serial
import logging
from typing import Optional, Tuple, Dict, List
import json

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
        self.calibration_offset = 0

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
                #print(f"Attempt {attempt + 1} failed: {e}")
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
            #print(error)
            return {"status": "INACTIVE", "errors": [error]}

    def parse_imu_data(self, line: str, cap_rotations=True) -> Tuple[List[float], List[float]]:
        """
        Parse IMU JSON data.
        Example line: {"gyroscope":[0.04,0.03,0.06],"orientation":[-55.69,-7.44,-12.08],"bms_voltage":10,"bms_current":20.60902,"bms_temp":21.2178} -> Format: [x, y, z] in rad/s, [Yaw, Pitch, Roll] in deg
        """
        try:
            data = json.loads(line)
        except json.JSONDecodeError as e:
            #print(f"JSON decode error: {e} for line: {line}")
            return [], [], None, None, None

        gyroscope = data.get("gyroscope", [])
        for i in range(len(gyroscope)):
            gyroscope[i] = math.degrees(gyroscope[i])
        orientation = data.get("orientation", [])
        bms_voltage = data.get("bms_voltage", None)
        bms_current = data.get("bms_current", None)
        bms_temp = data.get("bms_temp", None)

        if orientation:
            orientation[0] = (orientation[0] + self.calibration_offset)
            if cap_rotations:
                orientation = [val % 360 for val in orientation ]
        return gyroscope, orientation, bms_voltage, bms_current, bms_temp

    def get_imu_data(self, cap_rotations = True, max_attempts: int = 3) -> Dict[str, Optional[List[float]] | List[str]]:
        """Fetch IMU data with error handling."""
        errors = []
        for attempt in range(max_attempts):
            line = self.get_serial_text()
            if not line:
                errors.append(f"Attempt {attempt + 1}: No data received")
                continue
            
            gyro, orient, bms_voltage, bms_current, bms_temp = self.parse_imu_data(line, cap_rotations)
            if gyro or orient:  # At least one dataset is valid
                return {"gyroscope": gyro, "orientation": orient, "bms_voltage": bms_voltage, "bms_current": bms_current, "bms_temp": bms_temp , "errors": errors}
            else:
                errors.append(f"Attempt {attempt + 1}: Invalid data format")
        
        return {"gyroscope": None, "orientation": None, "errors": errors}

    def get_orientation(self, cap_rotations=True) -> List[float]:
        """Get orientation (convenience method)."""
        imu_data = self.get_imu_data(cap_rotations)
        if imu_data["orientation"] is None:
            raise ValueError(f"No orientation data. Errors: {imu_data['errors']}")
        return imu_data["orientation"]

    def get_current_yaw(self):
        orientation_data= self.get_orientation(cap_rotations=False)
        yaw = orientation_data[0]
        return yaw
    
    def get_current_angular_velocity(self):
        """Get current angular velocity (gyroscope data)."""
        imu_data = self.get_imu_data()
        if imu_data["gyroscope"] is None:
            raise ValueError(f"No gyroscope data. Errors: {imu_data['errors']}")
        return imu_data["gyroscope"][2]  # Return only the Z-axis value

    def get_bms_data(self):
        """Get BMS data (voltage, current, temperature)."""
        imu_data = self.get_imu_data()
        return imu_data.get("bms_voltage"), imu_data.get("bms_current"), imu_data.get("bms_temp")

    def send_command(self, command: str) -> None:
        """Send a command (e.g., 'CALIBRATE')."""
        if not self.serial_connection.is_open:
            raise serial.SerialException("Serial port not open")
        self.serial_connection.write(f"{command}\n".encode('utf-8'))
        self.serial_connection.flush()

    def calibrate(self) -> None:
        """Trigger calibration."""
        self.send_command('CALIBRATE')
        time.sleep(0.3)
        attempts = 0
        calibrating = True
        complete = False
        while calibrating and attempts < 4:
            line = self.get_serial_text()
            if line:
                if "complete" in line:
                    calibrating = False
                    complete = True
            else:
                attempts += 1
        return complete

    def set_calibration_offset(self, offset: float) -> None:
        """Set calibration offset for orientation."""

        if offset >= 0 and offset < 360:
            self.calibration_offset = offset
        else:
            raise ValueError("Offset must be in the range [0, 360) degrees")

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