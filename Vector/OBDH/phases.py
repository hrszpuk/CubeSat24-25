from time import time
from scipy import stats

def run_phase2(obdh, manager, logger, sequence):
    logger.info("Starting Phase 2")

    # 1- Start ADCS rotation
    manager.send("ADCS", "phase2_rotate")
    logger.info("ADCS rotation started")

    # 2- Wait for instruction from ADCS to take picture
    rotating = True

    while rotating:
        adcs_response = manager.receive("ADCS")
        cmd = adcs_response["command"]
        args = adcs_response["arguments"]

        if cmd == "take_picture":
            logger.info("ADCS instructed to take picture")
            manager.send("Payload", "take_picture", args={"current_yaw": args["current_yaw"]})
        elif cmd == "rotation_complete":
            logger.info("ADCS rotation complete, proceeding to image processing")
            rotating = False

    # 3- Process images
    manager.send("Payload", "get_numbers")
    numbers = manager.receive(name="Payload")["response"]
    logger.info(f"Payload numbers: {numbers}")

    # 4- send the sequence number to ADCS

    data = []
    number_distances = []
    degree_distances = []

    waiting_for_completion = True
    manager.send("ADCS", "phase2_sequence", {"sequence" : sequence, "numbers" : numbers})
    while waiting_for_completion and obdh.phase == OBDH.Phase.SECOND:
        adcs_response = manager.receive("ADCS")
        cmd = adcs_response["command"]

        if cmd == "take_distance":
            logger.info("ADCS instructed to take distance")
            manager.send("Payload", "take_distance")
            number_distance = manager.receive(name="Payload")["response"]
            number_distances.append(number_distance)
        elif cmd == "sequence_rotation_complete":
            logger.info("ADCS sequence rotation complete")
            waiting_for_completion = False

    adcs_response = manager.receive(name="ADCS")
    if adcs_response["command"] != "phase2_sequence_response":
        logger.error("Unexpected command from ADCS during phase 2 sequence")
    degree_distances = adcs_response["response"]

    for i, distance in enumerate(number_distances):
        data[sequence[i]] = {
            "angle_degree": numbers[sequence[i] if i < len(numbers) else None],
            "distance to number in cm": distance,
            "angle_variation": degree_distances[i] if i < len(degree_distances) else None
        }
    manager.send(name="TTC", msg="send_message", message={"data": data})

def run_phase3a(obdh, manager, logger):
    # Search for target, if timeout occurs, return to OBDH
    logger.info("Starting Phase 3a: Search for target")
    manager.send("ADCS", "phase3_search_target")

    initial_time = None
    distance_data = {}
    distance_data_backup = {}
    read_target = False 

    while obdh.phase == OBDH.Phase.THIRD and obdh.subphase == OBDH.SubPhase.A:
        adcs_response = manager.receive("ADCS")
        cmd = adcs_response["command"]
        args = adcs_response["arguments"]

        if cmd == "detect_apriltag":
            manager.send("Payload", "detect_apriltag")
            pose = manager.receive("Payload")["response"]
            if pose is not None:
                manager.send("ADCS", "apriltag_detected", {"pose": pose})
                if read_target:
                    if initial_time is None:
                        logger.info("Starting distance measurement")
                        initial_time = time.time()
                    current_time = time.time()
                    elapsed_time = int(current_time - initial_time)
                    if elapsed_time not in distance_data_backup.keys():
                        distance_data_backup[elapsed_time] = pose["translation"][2] # Assuming Z-axis is distance
        elif cmd == "target_found":
            manager.send("ADCS", "phase3_align_target", {"last_speed": args["last_speed"], "break_on_target_aligned": True})
        elif cmd == "target_aligned":
            read_target = True
        elif cmd == "timeout":
            logger.warning("Target search timed out. Subphase terminated.")
            obdh.subphase = None
            return 
        
        if read_target:
            if initial_time is None:
                logger.info("Starting distance measurement")
                initial_time = time.time()
            current_time = time.time()
            elapsed_time = int(current_time - initial_time)
            if elapsed_time not in distance_data.keys():
                manager.send("Payload", "take_distance")
                distance = manager.receive("Payload")["response"]
                distance_data[elapsed_time] = distance

    manager.send("ADCS", "stop_reaction_wheel")
    logger.info("Phase 3a completed, distance data collected")

    x = list(distance_data.keys())
    y = [val for val in distance_data.values() if isinstance(val, (int, float))]

    if x and y:
        slope, intercept, r, p, std_err = stats.linregress(x, y)
    else:
        slope, intercept, r, p, std_err = 0, 0, 0, 0, 0
        
    data = {
        "average_velocity": slope + " cm/s",
        "first_distance": y[0] if y else 0 + " cm",
        "last_distance": y[-1] if y else 0 + " cm",
        "raw_data": distance_data
    }

    x = list(distance_data_backup.keys())
    y = [val for val in distance_data_backup.values() if isinstance(val, (int, float))]

    if x and y:
        slope, intercept, r, p, std_err = stats.linregress(x, y)
    else:
        slope, intercept, r, p, std_err = 0, 0, 0, 0, 0
        
    backup_data = {
        "average_velocity": slope + " cm/s",
        "first_distance": y[0] if y else 0 + " cm",
        "last_distance": y[-1] if y else 0 + " cm",
        "raw_data": distance_data_backup
    }
    return data, backup_data

def run_phase3b(obdh, manager, logger):
    # reacquire target
    # If target is lost, search again
    # Assess target spin rate
    # take image of target
    # send image and spin rate

    manager.send("ADCS", "phase3_reacquire_target")

    initial_time = None
    spin_data = {}

    while obdh.phase == OBDH.Phase.THIRD and obdh.subphase == OBDH.SubPhase.B:
        adcs_response = manager.receive("ADCS")
        cmd = adcs_response["command"]
        args = adcs_response["arguments"]

        if cmd == "detect_apriltag":
            manager.send("Payload", "detect_apriltag")
            pose = manager.receive("Payload")["response"]
            if pose is not None:
                manager.send("ADCS", "apriltag_detected", {"pose": pose})
        elif cmd == "target_found":
            manager.send("ADCS", "phase3_align_target", {"last_speed": args["last_speed"], "break_on_target_aligned": False})
        elif cmd == "target_aligned":
            manager.send("ADCS", "phase3b_read_target")
        elif cmd == "reading_phase3b":
            adcs_rcv = manager.receive("ADCS")
            if adcs_rcv["command"] == "readings_phase3b":
                if initial_time is None:
                    logger.info("Starting measurement of spin rate")
                    initial_time = time.time()
                current_time = time.time()
                elapsed_time = int(current_time - initial_time)
                if elapsed_time not in spin_data.keys():
                    spin_data[elapsed_time] = adcs_rcv["arguments"]['yaw']
        elif cmd == "timeout":
            logger.warning("Target search timed out. Subphase terminated.")
            obdh.subphase = None
            return 

    manager.send("Payload", "take_picture_phase_3")
    path = manager.receive("Payload")["response"]

    manager.send("ADCS", "stop_reaction_wheel")
    logger.info("Phase 3b completed, spin data collected")

    x = list(spin_data.keys())
    y = [val for val in spin_data.values() if isinstance(val, (int, float))]

    if x and y:
        slope, intercept, r, p, std_err = stats.linregress(x, y)
    else:
        slope, intercept, r, p, std_err = 0, 0, 0, 0, 0

    spin_rate = slope

    manager.send("TTC", "send_picture", {"path": path})
    manager.send("TTC", "send_message", {
        "spin_rate": spin_rate + " degrees/s",
        "raw_data": spin_data
    })

def run_phase3c(obdh, manager, logger):
    #continuously align and measure distance to target
    # if target is lost, search again
    # send contact confirmation
    
    manager.send("ADCS", "phase3_reacquire_target")

    distance = 200

    while obdh.phase == OBDH.Phase.THIRD and obdh.subphase == OBDH.SubPhase.C and distance > 4:
        adcs_response = manager.receive("ADCS")
        cmd = adcs_response["command"]
        args = adcs_response["arguments"]

        if cmd == "detect_apriltag":
            manager.send("Payload", "detect_apriltag")
            pose = manager.receive("Payload")["response"]
            if pose is not None:
                manager.send("ADCS", "apriltag_detected", {"pose": pose})
        elif cmd == "target_found":
            manager.send("ADCS", "phase3_align_target", {"last_speed": args["last_speed"], "break_on_target_aligned": False})
        elif cmd == "target_aligned":
            manager.send("Payload", "take_distance")
            distance = manager.receive("Payload")["response"]
    manager.send("ADCS", "stop_reaction_wheel")
    logger.info("Phase 3c completed, docking completed")

    manager.send("TTC", "send_message", {"message": "Contact Confirmed"})