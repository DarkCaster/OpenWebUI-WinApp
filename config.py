import os


"""
Application configuration and constants.

Contains all configurable parameters and constants used throughout
the Open WebUI Launcher application.
"""

# Port number for open-webui service
# Read from PORT environment variable, default to 8080
PORT = int(os.getenv("PORT", "8080"))

# Time between health check attempts in seconds
HEALTH_CHECK_INTERVAL = 1.0

# Time to wait for graceful shutdown before force kill in seconds
SHUTDOWN_TIMEOUT = 10

# Maximum number of console output lines to keep in memory
MAX_CONSOLE_LINES = 1000

# Default window width in pixels
WINDOW_WIDTH = 1200

# Default window height in pixels
WINDOW_HEIGHT = 800

# Console panel height when visible in pixels
CONSOLE_HEIGHT = 200

# System tray icon title/tooltip text
SYSTEM_TRAY_TITLE = "Open WebUI Launcher"
