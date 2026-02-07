import requests
import threading
import time
from typing import Callable, Optional
from .logger import get_logger


class HealthChecker:
    """
    Monitor open-webui service availability via HTTP requests.

    Performs health checks by making HTTP GET requests to the service endpoint.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8080,
        interval: float = 1.0,
    ):
        """
        Initialize the health checker.

        Args:
            host: Host address to check (default: 127.0.0.1)
            port: Port number to check (default: 8080)
            interval: Time between health checks in seconds (default: 1.0)
        """
        self.host = host
        self.port = port
        self.interval = interval
        self.url = f"http://{host}:{port}"

        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._callback: Optional[Callable[[bool], None]] = None

        self.logger = get_logger(__name__)

    def check_availability(self) -> bool:
        """
        Perform a single health check attempt.

        Returns:
            True if service is available, False otherwise
        """
        try:
            response = requests.get(self.url, timeout=5)
            if response.status_code == 200:
                self.logger.debug(f"Health check successful: {self.url}")
                return True
            else:
                self.logger.debug(
                    f"Health check returned status {response.status_code}"
                )
                return False
        except requests.exceptions.RequestException as e:
            self.logger.debug(f"Health check failed: {e}")
            return False

    def start_monitoring(
        self, callback: Optional[Callable[[bool], None]] = None
    ) -> None:
        """
        Begin periodic health checks in a background thread.

        Args:
            callback: Optional callback function called with health check result
        """
        with self._lock:
            if self._monitoring:
                self.logger.warning("Monitoring already started")
                return

            self._monitoring = True
            self._callback = callback
            self._monitor_thread = threading.Thread(
                target=self._monitoring_loop, daemon=True, name="HealthMonitor"
            )
            self._monitor_thread.start()
            self.logger.info("Started health monitoring")

    def stop_monitoring(self) -> None:
        """
        Stop periodic health checks and wait for monitoring thread to finish.
        """
        with self._lock:
            if not self._monitoring:
                return

            self._monitoring = False

        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)
            self.logger.info("Stopped health monitoring")

    def _monitoring_loop(self) -> None:
        """
        Background thread loop for periodic health checks.
        Runs until stop_monitoring() is called.
        """
        self.logger.debug("Health monitoring loop started")

        while True:
            with self._lock:
                if not self._monitoring:
                    break

            is_available = self.check_availability()

            if self._callback:
                try:
                    self._callback(is_available)
                except Exception as e:
                    self.logger.error(f"Error in health check callback: {e}")

            time.sleep(self.interval)

        self.logger.debug("Health monitoring loop ended")
