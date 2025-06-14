from logger import get_logger
import time

def run_health_checks(manager):
    logger = get_logger()
    results = []

    output = manager.get_stdout("ADCS")
    name = "ADCS"

    try:
        lines = []
        start = time.time()
        while time.time() - start < 1:
            line = output.readline()
            if not line:
                break
            lines.append(line.strip())

        if lines:
            results.append(f"{name}: " + "\n".join(lines))
        else:
            results.append(f"{name}: No output received")

    except Exception as e:
        logger.error(f"{name} health check read failed: {e}")
        results.append(f"{name}: ERROR - {e}")

    return "\n".join(results)

