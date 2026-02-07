from enum import Enum


class ProcessState(str, Enum):
    """
    Enumeration of possible states for the Open WebUI process lifecycle.

    States:
        STOPPED: Process is not running
        STARTING: Process is launching, waiting for health check
        RUNNING: Process is running and healthy
        STOPPING: Process is being terminated
        ERROR: Process encountered an error
    """

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
