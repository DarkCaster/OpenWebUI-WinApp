import platform
import socket
import errno
import ctypes
from ctypes import wintypes

from .logger import get_logger


class SingleInstance:
    """
    Cross-platform single instance checker, ensures
    only one instance of the application is running.
    """

    def __init__(self, name: str):
        """
        Initialize the single instance checker.

        Args:
            name: A unique identifier for the application instance.
        """
        self._name = name
        self._lock = None
        self.logger = get_logger(__name__)

    def acquire(self) -> bool:
        """
        Attempt to acquire the single instance lock.

        Returns:
            True if this instance is the first/only one, False otherwise.
        """
        self.logger.debug(f"Attempting to acquire single instance lock: {self._name}")

        if platform.system() == "Windows":
            return self._acquire_windows()
        elif platform.system() == "Linux":
            return self._acquire_linux()
        else:
            # Fallback mechanism for other operating systems
            return self._acquire_fallback()

    def release(self) -> None:
        """
        Release the single instance lock.
        """
        self.logger.debug(f"Releasing single instance lock: {self._name}")

        if self._lock:
            if platform.system() == "Windows":
                self._release_windows()
            elif platform.system() == "Linux":
                self._release_linux()
            self._lock = None

    def _acquire_windows(self) -> bool:
        """
        Use Mutex to check for single instance on Windows.
        """
        # Define Windows API constants
        ERROR_ALREADY_EXISTS = 183
        # Import necessary functions
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        # Create a unique mutex name
        mutex_name = f"Global\\{self._name}"
        # Create the mutex
        lpName = wintypes.LPCWSTR(mutex_name)
        hMutex = kernel32.CreateMutexW(
            None,  # default security attributes
            wintypes.BOOL(True),  # initial owner
            lpName,
        )
        # Check if mutex creation failed
        if hMutex == 0:
            error_code = ctypes.get_last_error()
            self.logger.error(f"Failed to create mutex: Error code {error_code}")
            return False
        # Check if mutex already existed
        error_code = ctypes.get_last_error()
        if error_code == ERROR_ALREADY_EXISTS:
            self.logger.warning("Another instance is already running (Windows).")
            kernel32.CloseHandle(hMutex)
            return False
        # Successfully created the mutex, this instance is the leader
        self._lock = hMutex
        self.logger.info("Successfully acquired single instance lock (Windows).")
        return True

    def _release_windows(self) -> None:
        """
        Release and close the mutex handle on Windows.
        """
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        if self._lock and self._lock != 0:
            kernel32.ReleaseMutex(self._lock)
            kernel32.CloseHandle(self._lock)

    def _acquire_linux(self) -> bool:
        """
        Use Abstract Sockets to check for single instance on Linux.
        """
        # Abstract sockets start with '@'
        sock_name = f"@{self._name}"
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.bind(sock_name)
            sock.listen(1)
            self._lock = sock
            self.logger.info("Successfully acquired single instance lock (Linux).")
            return True
        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                self.logger.warning("Another instance is already running (Linux).")
                return False
            else:
                self.logger.error(f"Failed to bind abstract socket: {e}")
                return False
        except Exception as e:
            self.logger.error(f"Unexpected error acquiring lock on Linux: {e}")
            return False

    def _release_linux(self) -> None:
        """
        Close the socket on Linux.
        """
        if self._lock:
            try:
                self._lock.close()
            except Exception:
                pass

    # --- Fallback Implementation ---

    def _acquire_fallback(self) -> bool:
        """
        Fallback mechanism for OSes not explicitly supported.
        """
        self.logger.warning(
            f"Platform {platform.system()} not explicitly supported, using fallback."
        )
        # In a real project, you might implement a file lock here or raise an error
        return False
