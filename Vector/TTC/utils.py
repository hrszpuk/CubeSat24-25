import os
import tempfile
import zipfile
import re
import subprocess

def zip_file(file_path):    
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            zip_path = tmp.name

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write(file_path, os.path.basename(file_path))

    return zip_path

def get_connection_info(interface="wlan0"):
    try:
        result = subprocess.run(["sudo", "iwconfig", interface], capture_output=True, text=True, check=True)
        output = result.stdout
        connection_info = {
            "Downlink Frequency": None,
            "Uplink Frequency": None,
            "Signal Strength": None,
            "Data Transmission Rate": None
        }
        freq_match = re.search(r"Frequency:([\d.]+) GHz", output)

        if freq_match:
            connection_info["Downlink Frequency"] = float(freq_match.group(1))
            connection_info["Uplink Frequency"] = float(freq_match.group(1))

        signal_level_match = re.search(r"Signal level=(-\d+)\s+dBm", output)

        if signal_level_match:
            connection_info["Signal Strength"] = int(signal_level_match.group(1))

        bitrate_match = re.search(r"Bit Rate=(\d+\.?\d*)\s+Mb/s", output)

        if bitrate_match:
            connection_info["Data Transmission Rate"] = float(bitrate_match.group(1))

        return connection_info

    except subprocess.CalledProcessError as e:
        print(f"Error executing iwconfig for interface {interface}: {e}")
        print(f"Stderr: {e.stderr}")
        return None
    
    except FileNotFoundError:
        print(f"Error: 'iwconfig' command not found. Make sure wireless-tools is installed.")
        print(f"Install with: sudo apt install wireless-tools")
        return None
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None