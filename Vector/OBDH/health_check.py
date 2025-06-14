from logger import get_logger
import time

retries = 3
delay = 0.5

def run_health_checks(subsystems):
    logger = get_logger()
    report_lines = []

    for subsystem in subsystems:
        name = getattr(subsystem, 'name', repr(subsystem))
        for attempt in range(1, retries + 1):
            try:
                status = subsystem.health_check()
                report_lines.append(status)
                break
            except Exception as e:
                logger.warning(f"{name} health check attempt {attempt} failed: {e!r}")
                if attempt < retries:
                    time.sleep(delay)
                else:
                    err = f"{name} health CHECK FAILED after {retries} attempts: {e!r}"
                    logger.error(err)
                    report_lines.append(err)
    return "\n".join(report_lines)