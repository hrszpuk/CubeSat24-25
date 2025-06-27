from Vector.OBDH import logger


def run_phase2(manager, logger, sequence):
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
    while waiting_for_completion:
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

def run_phase3a(manager, logger):
    # Search for target, if timeout occurs, return to OBDH
    logger.info("Starting Phase 3a: Search for target")
    manager.send("ADCS", "phase3_search_target")

    #while self.get_state() == "IN_PHASE3A":
    while True: # Change this to a proper state check
        adcs_response = manager.receive("ADCS")
        cmd = adcs_response["command"]
        args = adcs_response["arguments"]

        if cmd == "detect_apriltag":
            manager.send("Payload", "detect_apriltag")
            pose = manager.receive("Payload")["response"]
            if pose is not None:
                manager.send("ADCS", "apriltag_detected", {"pose": pose})
        elif cmd == "apriltag_detected":
            manager.send("ADCS", "phase3_align_target", {"last_speed": args["last_speed"]})


        elif cmd == "timeout":
            logger.warning("Target search timed out, returning to OBDH")
            return
        
        
        
    
    # When target is found, align
    # If target is lost, search again
    # Measure distance to target
    # Get current velocity, rpm, velocity of incoming target
    # send data
    pass

def run_phase3b(manager, logger):
    # reacquire target
    # If target is lost, search again
    # Assess target spin rate
    # take image of target
    # send image and spin rate

    pass

def run_phase3c(manager, logger):
    #continuously align and measure distance to target
    # if target is lost, search again
    # send contact confirmation
    pass
