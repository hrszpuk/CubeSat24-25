import psutil
import datetime
import subprocess
import re
import os
import tempfile
import zipfile

def get_command_and_data_handling_status():
    memory = psutil.virtual_memory()
    boot_time_timestamp = psutil.boot_time()
    boot_time_datetime = datetime.datetime.fromtimestamp(boot_time_timestamp)
    current_time = datetime.datetime.now()
    uptime_delta = current_time - boot_time_datetime
    total_seconds = int(uptime_delta.total_seconds())
    minutes = total_seconds // 60

    return {"Memory Usage": memory.percent, "Uptime": minutes}

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
    
def zip_file(file_path):    
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            zip_path = tmp.name

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write(file_path, os.path.basename(file_path))

    return zip_path

def zip_folder(folder_path):
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            zip_path = tmp.name
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
         for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zip_file.write(file_path, os.path.relpath(file_path, folder_path))

    return zip_path