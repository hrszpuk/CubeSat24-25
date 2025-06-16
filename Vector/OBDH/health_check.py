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
    health_check_text += ("\n--- ADCS Subsystem ---\n")
    # for line in power_response[:-1]:
    #     health_check_text += line
    health_check_text += "\n"

    # Thermal Subsystem
    health_check_text += ("\n--- Thermal Subsystem ---\n")
    # for line in thermal_response[:-1]:
    #     health_check_text += line
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
    # for line in obdh_response[:-1]:
    #     health_check_text += line
    health_check_text += "\n"

    # Error Log
    health_check_text += ("\n--- Error Log ---\n")
    # for line in obdh_response[:-1]:
    #     health_check_text += line
    health_check_text += "\n"

    # Overall Status
    health_check_text += ("\n--- Overall Status ---\n")
    # for line in obdh_response[:-1]:
    #     health_check_text += line
    health_check_text += "\n"


    with open("health_check.txt", "w") as f:
        f.write(health_check_text)

