from ADCS.adcs_controller import AdcsController

import time, random

def start(pipe, log_queue):
    log_queue.put(("ADCS", "Starting Subsystem"))
    adcs_controller = AdcsController(log_queue)
    
    running = True
    while running:
        line, args = pipe.recv()
        if line == "health_check":
            variable = adcs_controller.health_check()
            pipe.send(variable)
        elif line == "test_wheel":
            kp = args["kp"]
            ki = args["ki"]
            kd = args["kd"]
            t = args["time"]
            degree = args["degree"]
            variable = adcs_controller.test_reaction_wheel(kp, ki, kd, t, degree)
            pipe.send(variable)
        elif line == "eps_health_check":
            variable = adcs_controller.get_eps_health_check()
            pipe.send(variable)
        elif line == "is_ready":
            variable = adcs_controller.get_state() == "READY"
            pipe.send(variable)
        elif line == "get_state":
            variable = adcs_controller.get_state()
            pipe.send(variable)
        elif line == "phase2_rotate":
            adcs_controller.phase2_rotate(pipe)
            pipe.send(("rotation_complete", None))
        elif line == "phase2_sequence":
            sequence = args.get("sequence", None)
            numbers = args.get("numbers", None)
            degree_distances = {}
            if sequence is None or numbers is None or len(sequence) == 0 or len(numbers) == 0:
                log_queue.put(("ADCS", "Error: Sequence or numbers not provided. Phase 2 Failed."))
            else:
                print(f"Received sequence: {sequence}, numbers: {numbers}")
                degree_distances = adcs_controller.phase2_sequence_rotation(pipe, sequence, numbers)
            print(f"INIT Degree distances: {degree_distances}")
            pipe.send(("sequence_rotation_complete", None))  # notify OBDH that sequence rotation is complete
            time.sleep(1)  # wait for a second before sending the response
            pipe.send(("phase2_sequence_response", {"degree_distances": degree_distances}))
        elif line == "phase3_search_target":
            adcs_controller.phase3_search_target(pipe)
        elif line == "phase3_reacquire_target":
            adcs_controller.phase3_reacquire_target(pipe)
        elif line == "phase3a_read_target":
            adcs_controller.phase3a_read_target(pipe)
        elif line == "phase3a_complete":
            current_wheel_velocity = adcs_controller.current_reaction_wheel.get_current_speed()
            current_satellite_velocity = adcs_controller.imu.get_current_angular_velocity()
            pipe.send(("readings_phase3a", {
                "current_wheel_velocity": current_wheel_velocity,
                "current_satellite_velocity": current_satellite_velocity
            }))
        elif line == "phase3b_read_target":
            adcs_controller.phase3b_read_target(pipe)
        elif line == "stop_reaction_wheel":
            adcs_controller.stop_reaction_wheel()
        elif line == "calibrate_sun_sensors":
            adcs_controller.calibrate_sun_sensors()
        elif line == "imu":
            imu_data = adcs_controller.imu.get_imu_data()
            pipe.send(imu_data)
        elif line == "stop":
            running = False
