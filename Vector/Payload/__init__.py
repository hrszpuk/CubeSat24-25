from Payload.payload_controller import PayloadController
from datetime import datetime
import threading
import time

TELEMETRY_INTERVAL = 3


def log_payload_data(controller, telemetry_queue, telemetry_stop_event):
    # NOTE(remy): since this is just statuses, the interval is higher
    # # and it'll only log to the queue if the status actually changes
    log_data = lambda label, data: telemetry_queue.put(("Payload", label, None, data))
    payload_status = controller.get_payload_status()
    log_data("status", payload_status)

    camera_status = controller.get_camera_status()
    for k, v in camera_status.items():
        log_data(k, v)

    while not telemetry_stop_event.is_set():
        payload_status_new = controller.get_payload_status()
        if payload_status != payload_status_new:
            payload_status = payload_status_new
            log_data(payload_status, telemetry_queue)

        camera_status_new = controller.get_camera_status()
        for k, v in camera_status.items():
            v2 = camera_status_new[k]
            if v != v2:
                camera_status[k] = v2
                log_data(k, v2)

        log_data(controller.get_payload_status(), telemetry_queue)
        time.sleep(TELEMETRY_INTERVAL)


def start(pipe, log_queue, telemetry_queue):
    log_queue.put(("Payload", "Starting Subsystem"))
    payload_controller = PayloadController(log_queue)

    telemetry_stop_event = threading.Event()

    t = threading.Thread(target=log_payload_data, args=(payload_controller, telemetry_queue, telemetry_stop_event))
    t.start()

    running = True
    while running:
        line, args = pipe.recv()
        if line == "health_check":
            variable = payload_controller.health_check()
            pipe.send(variable)
        elif line == "is_ready":
            variable = payload_controller.get_state() == "READY"
            pipe.send(variable)
        elif line == "get_state":
            variable = payload_controller.get_state()
            pipe.send(variable)
        elif line == "take_picture_raw":  # Used in payload_take_picture (OBDH, manual command)
            payload_controller.take_picture(args["dir"], args["name"])
        elif line == "take_picture":
            payload_controller.take_picture_phase_2(args["current_yaw"])
        elif line == "get_numbers":
            variable = payload_controller.identify_numbers_from_files()
            pipe.send(("numbers_identified", {"numbers_identified": variable}))
        elif line == "take_distance":
            variable = payload_controller.take_distance()
            pipe.send(variable)
        elif line == "detect_apriltag":
            variable = payload_controller.detect_apriltag()
            pipe.send(variable)
        elif line == "phase3_take_picture":
            path = payload_controller.stereo_camera.save_image()
            pipe.send(path)
        elif line == "stop":
            running = False

    telemetry_stop_event.set()
    t.join()


