import os


"""
Application configuration and constants.

Contains all configurable parameters and constants used throughout
the Open WebUI Launcher application.
"""

# Location of webview browser cache, cookies, local storage
WEB_STORAGE = os.getenv("WEB_STORAGE", os.getcwd())

# Host address for open-webui service
# Read from HOST environment variable, default to 127.0.0.1
HOST = os.getenv("HOST", "127.0.0.1")

# Port number for open-webui service
# Read from PORT environment variable, default to 8080
PORT = int(os.getenv("PORT", "8080"))

# Time to wait for graceful shutdown before force kill in seconds
SHUTDOWN_TIMEOUT = int(os.getenv("SHUTDOWN_TIMEOUT", "10"))

# Maximum number of console output lines to keep in memory
MAX_CONSOLE_LINES = int(os.getenv("MAX_CONSOLE_LINES", "1000"))

# Default window width in pixels
WINDOW_WIDTH = int(os.getenv("WINDOW_WIDTH", "1200"))

# Default window height in pixels
WINDOW_HEIGHT = int(os.getenv("WINDOW_HEIGHT", "960"))

# Open links in external browser, or directly in application window
OPEN_EXTERNAL_LINKS_IN_BROWSER = bool(
    os.getenv("OPEN_EXTERNAL_LINKS_IN_BROWSER", "True")
)

# Test page, for debug purposes
TEST_PAGE = os.getenv("TEST_PAGE", "")

# System tray icon title/tooltip text
SYSTEM_TRAY_TITLE = "Open WebUI Launcher"

# Unique identifier for single instance lock (used in OS-specific IPC)
SINGLE_INSTANCE_NAME = "OpenWebUILauncher"
