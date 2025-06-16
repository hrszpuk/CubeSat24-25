import datetime
from gpiozero import CPUTemperature
import psutil
import time

def run_health_checks(manager):
    manager.send("ADCS", "health_check")
    adcs_response = manager.receive("ADCS")
    manager.send("Payload", "health_check")
    payload_response = manager.receive("Payload")

    health_check_text = "--- Vector CubeSat Health Check Report ---\n"
    health_check_text += "Date: " + time.strftime("%d-%m-%Y") + "\n"
    health_check_text += "Time: " + time.strftime("%H:%M:%S", time.gmtime()) + " GMT\n"

    # Power Subsystem
    health_check_text += ("\n--- Power Subsystem ---\n")
    health_check_text += "Battery Voltage\n"
    health_check_text += "Battery Current\n"
    health_check_text += "Battery Temperature\n"
    # for line in power_response[:-1]:
    #     health_check_text += line
    health_check_text += "\n"

    # Thermal Subsystem
    cpu = CPUTemperature()

    health_check_text += ("\n--- Thermal Subsystem ---\n")
    if cpu.temperature > 80:
        health_check_text += f"Internal Temperature: {cpu.temperature:.2f}°C (CRITICAL)\n"
        health_check_text += "Status: CRITICAL - OVERHEATING\n"
    elif cpu.temperature > 70:
        health_check_text += f"Internal Temperature: {cpu.temperature:.2f}°C (WARNING)\n"
        health_check_text += "Status: WARNING - HIGH TEMPERATURE\n"
    else:
        health_check_text += f"Internal Temperature: {cpu.temperature:.2f}°C (NOMINAL)\n"
        health_check_text += "Status: OK\n"
    health_check_text += "\n"

    # Communication Subsystem
    health_check_text += ("\n--- Communication Subsystem ---\n")
    # for line in communication_response[:-1]:
    #     health_check_text += line
    health_check_text += "\n"

    # ADCS Subsystem
    health_check_text += ("\n--- ADCS Subsystem ---\n")
    for line in adcs_response[:-1]:
        health_check_text += line
    health_check_text += "\n"

    # Payload Subsystem
    health_check_text += ("\n--- Payload Subsystem ---\n")
    for line in payload_response[:-1]:
        health_check_text += line
    health_check_text += "\n"

    # Communication Subsystem
    health_check_text += ("\n--- Command and Data Handling Subsystem ---\n")
    memory = psutil.virtual_memory()
    boot_time_timestamp = psutil.boot_time()

    boot_time_datetime = datetime.datetime.fromtimestamp(boot_time_timestamp)
    current_time = datetime.datetime.now()

    uptime_delta = current_time - boot_time_datetime

    total_seconds = int(uptime_delta.total_seconds())
    minutes = total_seconds // 60
    
    health_check_text += f"Memory Usage: {memory.percent}%\n"
    health_check_text += f"Last Command Received: \n"
    health_check_text += f"Uptime: {minutes} minutes\n"

    # for line in obdh_response[:-1]:
    #     health_check_text += line
    health_check_text += "\n"

    # Error Log
    health_check_text += ("\n--- Error Log ---\n")
    errors = []
    # for line in obdh_response[:-1]:
    #     health_check_text += line
    health_check_text += "\n"

    # Overall Status
    health_check_text += ("\n--- Overall Status ---\n")
    if errors:
        health_check_text += "CRITICAL - Errors Detected\n"
        health_check_text += "Recommended actions: Check logs for details.\n"
    else:
        health_check_text += "NOMINAL - All systems operational\n"
        health_check_text += "Recommended actions: Continue standard operations.\n"
    health_check_text += "\n"
    health_check_text += "--- End of Report ---\n"


    with open("health.txt", "w") as f:
        f.write(health_check_text)

