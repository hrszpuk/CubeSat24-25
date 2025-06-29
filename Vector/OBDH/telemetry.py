import time
from threading import Thread

class Telemetry:
    def __init__(self, manager, interval=5):
        self.interval = interval
        self.manager = manager
        self.running = False

    def collect_telemetry(self):
        self.manager.send("ADCS", "health_check")
        health_check_text = self.manager.receive("ADCS")["response"]

        telemetry = ""
        for line in health_check_text.splitlines():
            if "Gyroscope" in line or "Orientation" in line or "Reaction Wheel" in line:
                telemetry += line + "\n"

        return telemetry

    def broadcast(self):
        while self.running:
            telemetry = self.collect_telemetry()
            self.manager.send("TTC", "send_message", {"message": f"[TELEMETRY]\n{telemetry}\n"})
            time.sleep(self.interval)

    def start(self):
        self.running = True
        thread = Thread(target=self.broadcast, daemon=True)
        thread.start()

    def stop(self):
        self.running = False
