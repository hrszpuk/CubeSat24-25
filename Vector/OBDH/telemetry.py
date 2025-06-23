import time
from threading import Thread

class Telemetry:
    def __init__(self, manager, ttc, interval=5):
        self.manager = manager
        self.ttc = ttc
        self.interval = interval
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
            conn = self.ttc.get_connection()
            if conn:
                try:
                    conn.sendall(f"[TELEMETRY]\n{telemetry}\n".encode('utf-8'))
                except Exception as e:
                    print(f"Failed to send telemetry: {e}")
            time.sleep(self.interval)

    def start(self):
        self.running = True
        thread = Thread(target=self.broadcast, daemon=True)
        thread.start()

    def stop(self):
        self.running = False
