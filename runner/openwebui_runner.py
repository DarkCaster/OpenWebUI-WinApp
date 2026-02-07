import subprocess
import threading
import os
import sys
import time
from datetime import datetime
from typing import Callable, List, Optional, TextIO
from app.logger import get_logger
from app.config import HOST, PORT
from .process_state import ProcessState
from .health_checker import HealthChecker


class OpenWebUIRunner:
    """
    Manage the open-webui serve subprocess lifecycle.

    Handles process creation, health monitoring, output capture,
    and graceful shutdown of the open-webui service.
    """

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        """
        Initialize the Open WebUI runner.

        Args:
            host: Host address for open-webui service (defaults to HOST env var or 127.0.0.1)
            port: Port number for open-webui service (defaults to PORT env var or 8080)
        """
        self.host = host or HOST
        self.port = port or PORT

        self._process: Optional[subprocess.Popen] = None
        self._state = ProcessState.STOPPED
        self._state_lock = threading.Lock()

        self._output_lines: List[str] = []
        self._output_lock = threading.Lock()
        self._output_thread: Optional[threading.Thread] = None

        self._log_file: Optional[TextIO] = None
        self._log_file_lock = threading.Lock()

        self._output_subscribers: List[Callable[[str], None]] = []
        self._state_subscribers: List[Callable[[ProcessState, ProcessState], None]] = []

        self._health_checker = HealthChecker(
            host=self.host, port=self.port, interval=1.0
        )

        self.logger = get_logger(__name__)
        self.logger.info(
            f"OpenWebUIRunner initialized with host {self.host} and port {self.port}"
        )

    def start(self) -> bool:
        """
        Launch the open-webui process.

        Returns:
            True if process started successfully, False otherwise
        """
        with self._state_lock:
            if self._state != ProcessState.STOPPED:
                self.logger.warning(f"Cannot start: current state is {self._state}")
                return False

            self._set_state(ProcessState.STARTING)

        try:
            # Open log file
            try:
                self._log_file = open("open-webui.log", "a", encoding="utf-8")
                self.logger.debug("Opened log file: open-webui.log")
            except Exception as e:
                self.logger.error(f"Failed to open log file: {e}")
                self._set_state(ProcessState.ERROR)
                return False

            # Write separator
            self._write_separator("STARTING")

            self.logger.info(
                f"Starting open-webui serve on host {self.host} and port {self.port}"
            )

            # Prepare environment with UTF-8 encoding
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            # Launch subprocess using Python interpreter to run startup script
            # Generate path to start_openwebui.py in the same directory as this script
            start_script_path = os.path.join(
                os.path.dirname(__file__), "start_openwebui.py"
            )
            self._process = subprocess.Popen(
                [
                    sys.executable,
                    start_script_path,
                    "--host",
                    self.host,
                    "--port",
                    str(self.port),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=env,
            )

            self.logger.debug(f"Process started with PID: {self._process.pid}")

            # Start output reader thread
            self._output_thread = threading.Thread(
                target=self._output_reader_thread, daemon=True, name="OutputReader"
            )
            self._output_thread.start()

            # Wait for health check in background
            health_thread = threading.Thread(
                target=self._wait_for_health, daemon=True, name="HealthWaiter"
            )
            health_thread.start()

            return True

        except FileNotFoundError as e:
            self.logger.error(
                f"Failed to start open-webui: Startup script not found. Error: {e}"
            )
            self._close_log_file()
            self._set_state(ProcessState.ERROR)
            return False
        except PermissionError as e:
            self.logger.error(
                f"Failed to start open-webui: Permission denied. Error: {e}"
            )
            self._close_log_file()
            self._set_state(ProcessState.ERROR)
            return False
        except OSError as e:
            self.logger.error(
                f"Failed to start open-webui: OS error occurred. Error: {e}"
            )
            self._close_log_file()
            self._set_state(ProcessState.ERROR)
            return False
        except Exception as e:
            self.logger.error(f"Failed to start open-webui: Unexpected error: {e}")
            self._close_log_file()
            self._set_state(ProcessState.ERROR)
            return False

    def stop(self, timeout: int = 10) -> bool:
        """
        Gracefully terminate the open-webui process.

        Args:
            timeout: Time to wait for graceful shutdown before force kill

        Returns:
            True if process stopped successfully, False otherwise
        """
        with self._state_lock:
            if self._state in (ProcessState.STOPPED, ProcessState.STOPPING):
                self.logger.warning(f"Cannot stop: current state is {self._state}")
                return False

            self._set_state(ProcessState.STOPPING)

        # Write separator
        self._write_separator("STOPPING")

        if not self._process:
            self._write_separator("STOPPED")
            self._close_log_file()
            self._set_state(ProcessState.STOPPED)
            return True

        try:
            self.logger.info("Stopping open-webui process")

            # Try graceful termination
            if self._process.poll() is None:
                self.logger.debug("Sending SIGTERM")
                self._process.terminate()

                try:
                    self._process.wait(timeout=timeout)
                    self.logger.info("Process terminated gracefully")
                except subprocess.TimeoutExpired:
                    self.logger.warning(
                        f"Process did not terminate within {timeout}s, forcing kill"
                    )
                    self._process.kill()
                    self._process.wait(timeout=5)
                    self.logger.info("Process killed forcefully")

            # Wait for output thread to finish
            if self._output_thread and self._output_thread.is_alive():
                self._output_thread.join(timeout=2)

            self._process = None
            self._write_separator("STOPPED")
            self._close_log_file()
            self._set_state(ProcessState.STOPPED)
            return True

        except Exception as e:
            self.logger.error(f"Error stopping process: {e}")
            self._close_log_file()
            self._set_state(ProcessState.ERROR)
            return False

    def restart(self) -> bool:
        """
        Stop and start the open-webui process.

        Returns:
            True if restart successful, False otherwise
        """
        self.logger.info("Restarting open-webui")
        self._write_separator("RESTARTING")

        # Check current state
        current_state = self.get_state()

        # Only stop if process is in a state that requires stopping
        if current_state in (
            ProcessState.STARTING,
            ProcessState.RUNNING,
            ProcessState.STOPPING,
        ):
            if not self.stop():
                self.logger.error("Failed to stop process during restart")
                return False
            # Give a brief moment for cleanup
            time.sleep(1)
        elif current_state in (ProcessState.STOPPED, ProcessState.ERROR):
            # Process is already stopped or in error state, skip stop step
            self.logger.debug(
                f"Process is in {current_state} state, skipping stop step"
            )
        else:
            # Unexpected state
            self.logger.warning(f"Unexpected state during restart: {current_state}")

        if not self.start():
            self.logger.error("Failed to start process during restart")
            return False

        return True

    def get_state(self) -> ProcessState:
        """
        Get the current process state.

        Returns:
            Current ProcessState
        """
        with self._state_lock:
            return self._state

    def get_output_lines(self, max_lines: Optional[int] = None) -> List[str]:
        """
        Get captured console output lines.

        Args:
            max_lines: Maximum number of lines to return (most recent), None for all

        Returns:
            List of output lines
        """
        with self._output_lock:
            if max_lines is None:
                return self._output_lines.copy()
            else:
                return self._output_lines[-max_lines:]

    def subscribe_to_output(self, callback: Callable[[str], None]) -> None:
        """
        Register callback for new output lines.

        Args:
            callback: Function to call with each new output line
        """
        self._output_subscribers.append(callback)
        self.logger.debug(f"Output subscriber registered: {callback.__name__}")

    def subscribe_to_state_change(
        self, callback: Callable[[ProcessState, ProcessState], None]
    ) -> None:
        """
        Register callback for state changes.

        Args:
            callback: Function to call with (old_state, new_state)
        """
        self._state_subscribers.append(callback)
        self.logger.debug(f"State change subscriber registered: {callback.__name__}")

    def _set_state(self, new_state: ProcessState) -> None:
        """
        Set process state and notify subscribers (thread-safe).

        Args:
            new_state: New ProcessState to transition to
        """
        old_state = self._state
        self._state = new_state

        if old_state != new_state:
            self.logger.info(f"State transition: {old_state} -> {new_state}")

            for callback in self._state_subscribers:
                try:
                    callback(old_state, new_state)
                except Exception as e:
                    self.logger.error(f"Error in state change callback: {e}")

    def _output_reader_thread(self) -> None:
        """
        Background thread to read subprocess output continuously.
        Runs until process terminates or stdout is closed.
        """
        self.logger.debug("Output reader thread started")

        if not self._process or not self._process.stdout:
            self.logger.error("No process or stdout available")
            return

        try:
            for line in iter(self._process.stdout.readline, ""):
                if not line:
                    break

                line = line.rstrip()

                with self._output_lock:
                    self._output_lines.append(line)

                # Write to log file
                with self._log_file_lock:
                    if self._log_file:
                        try:
                            self._log_file.write(line + "\n")
                            self._log_file.flush()
                        except Exception as e:
                            self.logger.error(f"Error writing to log file: {e}")

                self._notify_output_subscribers(line)

        except Exception as e:
            self.logger.error(f"Error reading process output: {e}")
        finally:
            # Check if process terminated
            if self._process:
                self._process.poll()
            self.logger.debug("Output reader thread ended")

    def _notify_output_subscribers(self, line: str) -> None:
        """
        Notify all output subscribers of a new line.

        Args:
            line: New output line
        """
        for callback in self._output_subscribers:
            try:
                callback(line)
            except Exception as e:
                self.logger.error(f"Error in output callback: {e}")

    def _wait_for_health(self) -> None:
        """
        Wait for service to become healthy and update state accordingly.
        Runs in background thread after process start.
        Waits indefinitely until service starts, process terminates, or state changes.
        """
        self.logger.debug("Waiting for health check (no timeout)")

        # Give process a moment to start
        time.sleep(0.5)

        # Check if process is still alive before starting health check
        if self._process and self._process.poll() is not None:
            exit_code = self._process.returncode
            self.logger.error(
                f"Process terminated before health check could complete. Exit code: {exit_code}"
            )

            with self._state_lock:
                if self._state == ProcessState.STARTING:
                    self._set_state(ProcessState.ERROR)
            return

        # Perform health check with periodic process monitoring (indefinitely)
        start_time = time.time()
        while True:
            # Check if state has changed from STARTING (user called stop/restart)
            with self._state_lock:
                if self._state != ProcessState.STARTING:
                    self.logger.info(
                        f"Health check stopped due to state change to {self._state}"
                    )
                    return

            # Check if process is still running
            if self._process and self._process.poll() is not None:
                exit_code = self._process.returncode
                self.logger.error(
                    f"Process terminated during health check. Exit code: {exit_code}"
                )

                with self._state_lock:
                    if self._state == ProcessState.STARTING:
                        self._set_state(ProcessState.ERROR)
                return

            # Try health check
            if self._health_checker.check_availability():
                elapsed = time.time() - start_time
                self.logger.info(f"Service became available after {elapsed:.1f}s")
                with self._state_lock:
                    if self._state == ProcessState.STARTING:
                        self._set_state(ProcessState.RUNNING)
                return

            time.sleep(self._health_checker.interval)

    def _write_separator(self, action: str) -> None:
        """
        Write a separator line to both console and log file.

        Args:
            action: Action description (e.g., "STARTING", "STOPPING", "STOPPED")
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        separator = f"{'=' * 80}\n{timestamp} - {action}\n{'=' * 80}"

        # Write to output lines
        with self._output_lock:
            for line in separator.split("\n"):
                self._output_lines.append(line)
                self._notify_output_subscribers(line)

        # Write to log file
        with self._log_file_lock:
            if self._log_file:
                try:
                    self._log_file.write(separator + "\n")
                    self._log_file.flush()
                except Exception as e:
                    self.logger.error(f"Error writing separator to log file: {e}")

    def _close_log_file(self) -> None:
        """
        Close the log file if it's open.
        """
        with self._log_file_lock:
            if self._log_file:
                try:
                    self._log_file.close()
                    self.logger.debug("Closed log file")
                except Exception as e:
                    self.logger.error(f"Error closing log file: {e}")
                finally:
                    self._log_file = None
