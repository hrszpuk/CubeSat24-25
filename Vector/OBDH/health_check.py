from logger import get_logger

def run_health_checks(subsystems):
    logger = get_logger()
    report_lines = []

    for subsystem in subsystems:
        name = getattr(subsystem, 'name')
        try:
            subsystemStatus = subsystem.health_check()
            report_lines.append(subsystemStatus)
        except Exception as e:
            err = f"{name} health CHECK FAILED: {e!r}"
            logger.error(err)
            report_lines.append(err)
    return "\n".join(report_lines)