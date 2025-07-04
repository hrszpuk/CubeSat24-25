import glob
import os
from time import time
from scipy import stats
from enums import OBDHState, Phase, SubPhase

def run_phase2(obdh, manager, logger, sequence):
    logger.info("Starting Phase 2")

    # 1- Start ADCS rotation
    manager.send("ADCS", "phase2_rotate")
    logger.info("ADCS rotation started")

    # 2- Wait for instruction from ADCS to take picture
    rotating = True

    while rotating:
        adcs_response = manager.receive("ADCS")
        print(adcs_response)
        cmd = adcs_response["command"]
        args = adcs_response["arguments"]

        if cmd == "take_picture":
            logger.info("ADCS instructed to take picture")
            manager.send("Payload", "take_picture", args={"current_yaw": args["current_yaw"]})
        elif cmd == "rotation_complete":
            logger.info("ADCS rotation complete, proceeding to image processing")
            rotating = False

    # 3- Process images
    processing_images = True
    manager.send("Payload", "get_numbers")
    
    while processing_images:
        if manager.pipes["Payload"].poll():
            numbers = manager.receive(name="Payload")["arguments"]["numbers_identified"]
            logger.info(f"Numbers Identified: {numbers}")
            processing_images = False

    # 4- send the sequence number to ADCS

    data = []
    number_distances = []
    degree_distances = []

    targets = {}
    keys = list(numbers.keys())
    found_sequence = []

    for n in sequence:
        if n in keys:
            targets[n] = numbers[n]
            found_sequence.append(n)

    logger.info(f"Original sequence: {sequence}, Found numbers: {found_sequence}")
    
    waiting_for_completion = True

    manager.send("ADCS", "phase2_sequence", {"sequence" : found_sequence, "numbers" : targets})
    while waiting_for_completion and obdh.phase == Phase.SECOND:
        adcs_response = manager.receive("ADCS")
        logger.info(f"ADCS response: {adcs_response}")
        cmd = adcs_response["command"]

        if cmd == "take_distance":
            logger.info("ADCS instructed to take distance")
            manager.send("Payload", "take_distance")
            number_distance = manager.receive(name="Payload")["response"]
            number_distances.append(number_distance)
        elif cmd == "take_picture_rotation":
            manager.send("Payload", "take_distance_rotation")
        elif cmd == "sequence_rotation_complete":
            logger.info("ADCS sequence rotation complete")
            waiting_for_completion = False

    adcs_response = manager.receive(name="ADCS")
    if adcs_response["command"] != "phase2_sequence_response":
        logger.error("Unexpected command from ADCS during phase 2 sequence")
    degree_distances = adcs_response["arguments"]["degree_distances"]

    print(f"Number distances: {number_distances}")

    for i, distance in enumerate(number_distances):
        data.append({
            "number": sequence[i] if i < len(sequence) else None,
            "angle_degree": numbers[sequence[i] if i < len(numbers) else None],
            "number": found_sequence[i] if i < len(found_sequence) else None,
            "angle_degree": numbers[found_sequence[i]] if i < len(found_sequence) and found_sequence[i] in numbers else None,
            "distance to number in cm": distance,
            "angle_variation": degree_distances[i] if i < len(degree_distances) else None
        })

    # image_paths = glob.glob("images/phase2/*.jpg")
    # for path in image_paths:
    #     os.remove(path)  # Clean up images after processing
    manager.send("TTC", "send_message", {"message": data if data else "No data collected"})

def run_phase3a(obdh, manager, logger):
    # Search for target, if timeout occurs, return to OBDH
    logger.info("Starting Phase 3a: Search for target")
    manager.send("ADCS", "phase3_search_target")

    align_timer = None
    distance_data = {}
    distance_data_backup = {}
    read_target = False 

    while obdh.phase == Phase.THIRD and obdh.subphase == SubPhase.a:
        adcs_response = manager.receive("ADCS")
        cmd = adcs_response["command"]
        args = adcs_response["arguments"]

        if cmd == "detect_apriltag":
            manager.send("Payload", "detect_apriltag", log=False)
            pose = manager.receive("Payload")["response"]
            if pose is not None:
                manager.send("ADCS", "apriltag_detected", {"pose": pose}, log=False)
                if read_target:
                    if align_timer is None:
                        logger.info("Starting distance measurement")
                        align_timer = time.time()
                    current_time = time.time()
                    elapsed_time = int(current_time - align_timer)
                    if elapsed_time not in distance_data_backup.keys():
                        distance_data_backup[elapsed_time] = pose["translation"][2] # Assuming Z-axis is distance
            else:
                manager.send("ADCS", "apriltag_not_detected", log=False)
        elif cmd == "target_found":
            manager.send("ADCS", "phase3_align_target", {"current_tag_yaw": args["current_tag_yaw"], "break_on_target_aligned": True})
        elif cmd == "target_aligned":
            read_target = True
        elif cmd == "target_lost":
            read_target = False
            manager.send("ADCS", "phase3_search_target")
        elif cmd == "timeout":
            logger.warning("Target search timed out. Subphase terminated.")
            obdh.subphase = None
            return None, None
        
        current_time = time.time()
        if read_target:
            if current_time - (align_timer if align_timer else 0) < 30:
                if align_timer is None:
                    logger.info("Starting distance measurement")
                    align_timer = time.time()
                elapsed_time = int(current_time - align_timer)
                if elapsed_time not in distance_data.keys():
                    manager.send("Payload", "take_distance")
                    distance = manager.receive("Payload")["response"]
                    distance_data[elapsed_time] = distance
            else:
                logger.info("Stopping distance measurement after 30 seconds")
                read_target = False
                align_timer = None
                manager.send("ADCS", "stop_reaction_wheel", log=False)

        # if read_target:
        #     if initial_time is None:
        #         logger.info("Starting distance measurement")
        #         initial_time = time.time()
        #     current_time = time.time()
        #     elapsed_time = int(current_time - initial_time)
        #     if elapsed_time not in distance_data.keys():
        #         manager.send("Payload", "take_distance")
        #         distance = manager.receive("Payload")["response"]
        #         distance_data[elapsed_time] = distance

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

    while obdh.phase == Phase.THIRD and obdh.subphase == SubPhase.b:
        adcs_response = manager.receive("ADCS")
        cmd = adcs_response["command"]
        args = adcs_response["arguments"]

        if cmd == "detect_apriltag":
            manager.send("Payload", "detect_apriltag")
            pose = manager.receive("Payload")["response"]
            if pose is not None:
                manager.send("ADCS", "apriltag_detected", {"pose": pose})
            else:
                manager.send("ADCS", "apriltag_not_detected")
        elif cmd == "target_found":
            manager.send("ADCS", "phase3_align_target", {"break_on_target_aligned": False})
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

    while obdh.phase == Phase.THIRD and obdh.subphase == SubPhase.c and distance > 4:
        adcs_response = manager.receive("ADCS")
        cmd = adcs_response["command"]
        args = adcs_response["arguments"]

        if cmd == "detect_apriltag":
            manager.send("Payload", "detect_apriltag")
            pose = manager.receive("Payload")["response"]
            if pose is not None:
                manager.send("ADCS", "apriltag_detected", {"pose": pose})
            else:
                manager.send("ADCS", "apriltag_not_detected")
        elif cmd == "target_found":
            manager.send("ADCS", "phase3_align_target", {"break_on_target_aligned": False})
        elif cmd == "target_aligned":
            manager.send("Payload", "take_distance")
            distance = manager.receive("Payload")["response"]
            manager.send("ADCS", "phase3c_read_target", {"distance": distance})
    manager.send("ADCS", "stop_reaction_wheel")
    logger.info("Phase 3c completed, docking completed")

    manager.send("TTC", "send_message", {"message": "Contact Confirmed"})