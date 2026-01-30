import subprocess
import threading
import os
import time
from typing import Callable, List, Optional
from logger import get_logger
from .process_state import ProcessState
from .health_checker import HealthChecker


class OpenWebUIRunner:
    """
    Manage the open-webui serve subprocess lifecycle.

    Handles process creation, health monitoring, output capture,
    and graceful shutdown of the open-webui service.
    """

    def __init__(self, port: Optional[int] = None, health_check_timeout: int = 60):
        """
        Initialize the Open WebUI runner.

        Args:
            port: Port number for open-webui service (defaults to PORT env var or 8080)
            health_check_timeout: Maximum time to wait for service health check
        """
        self.port = port or int(os.getenv("PORT", "8080"))
        self.health_check_timeout = health_check_timeout

        self._process: Optional[subprocess.Popen] = None
        self._state = ProcessState.STOPPED
        self._state_lock = threading.Lock()

        self._output_lines: List[str] = []
        self._output_lock = threading.Lock()
        self._output_thread: Optional[threading.Thread] = None

        self._output_subscribers: List[Callable[[str], None]] = []
        self._state_subscribers: List[Callable[[ProcessState, ProcessState], None]] = []

        self._health_checker = HealthChecker(
            host="127.0.0.1", port=self.port, timeout=health_check_timeout, interval=1.0
        )

        self.logger = get_logger(__name__)
        self.logger.info(f"OpenWebUIRunner initialized with port {self.port}")

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
            self.logger.info(f"Starting open-webui serve on port {self.port}")

            # Launch subprocess
            self._process = subprocess.Popen(
                ["open-webui", "serve", "--port", str(self.port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
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
            self.logger.error(f"Failed to start open-webui: Command not found. Is 'open-webui' installed? Error: {e}")
            self._set_state(ProcessState.ERROR)
            return False
        except PermissionError as e:
            self.logger.error(f"Failed to start open-webui: Permission denied. Error: {e}")
            self._set_state(ProcessState.ERROR)
            return False
        except OSError as e:
            self.logger.error(f"Failed to start open-webui: OS error occurred. Error: {e}")
            self._set_state(ProcessState.ERROR)
            return False
        except Exception as e:
            self.logger.error(f"Failed to start open-webui: Unexpected error: {e}")
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

        if not self._process:
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
            self._set_state(ProcessState.STOPPED)
            return True

        except Exception as e:
            self.logger.error(f"Error stopping process: {e}")
            self._set_state(ProcessState.ERROR)
            return False

    def restart(self) -> bool:
        """
        Stop and start the open-webui process.

        Returns:
            True if restart successful, False otherwise
        """
        self.logger.info("Restarting open-webui")

        if not self.stop():
            self.logger.error("Failed to stop process during restart")
            return False

        # Give a brief moment for cleanup
        time.sleep(1)

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

                self._notify_output_subscribers(line)

        except Exception as e:
            self.logger.error(f"Error reading process output: {e}")
        finally:
            # Check if process terminated abnormally
            if self._process:
                exit_code = self._process.poll()
                if exit_code is not None and exit_code != 0:
                    self.logger.error(f"Process terminated with exit code: {exit_code}")
                    # Log last few lines of output
                    last_lines = self.get_output_lines(max_lines=20)
                    if last_lines:
                        self.logger.error("Last output lines from process:")
                        for line in last_lines:
                            self.logger.error(f"  {line}")
                elif exit_code == 0:
                    self.logger.info("Process terminated normally with exit code: 0")

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
        """
        self.logger.debug("Waiting for health check")

        # Give process a moment to start
        time.sleep(0.5)

        # Check if process is still alive before starting health check
        if self._process and self._process.poll() is not None:
            exit_code = self._process.returncode
            self.logger.error(f"Process terminated before health check could complete. Exit code: {exit_code}")
            
            # Log recent output
            last_lines = self.get_output_lines(max_lines=20)
            if last_lines:
                self.logger.error("Recent output from process:")
                for line in last_lines:
                    self.logger.error(f"  {line}")
            else:
                self.logger.error("No output was captured from the process")
            
            with self._state_lock:
                if self._state == ProcessState.STARTING:
                    self._set_state(ProcessState.ERROR)
            return

        # Perform health check with periodic process monitoring
        start_time = time.time()
        while time.time() - start_time < self.health_check_timeout:
            # Check if process is still running
            if self._process and self._process.poll() is not None:
                exit_code = self._process.returncode
                self.logger.error(f"Process terminated during health check. Exit code: {exit_code}")
                
                # Log recent output
                last_lines = self.get_output_lines(max_lines=20)
                if last_lines:
                    self.logger.error("Recent output from process:")
                    for line in last_lines:
                        self.logger.error(f"  {line}")
                else:
                    self.logger.error("No output was captured from the process")
                
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

        # Timeout reached
        self.logger.error("Health check timeout")
        
        # Check if process is still running
        if self._process:
            exit_code = self._process.poll()
            if exit_code is not None:
                self.logger.error(f"Process has exited with code: {exit_code}")
            else:
                self.logger.error("Process is still running but not responding to health checks")
        
        # Log recent output
        last_lines = self.get_output_lines(max_lines=20)
        if last_lines:
            self.logger.error("Recent output from process:")
            for line in last_lines:
                self.logger.error(f"  {line}")
        else:
            self.logger.error("No output was captured from the process")
        
        with self._state_lock:
            if self._state == ProcessState.STARTING:
                self._set_state(ProcessState.ERROR)
