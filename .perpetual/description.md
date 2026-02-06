# Open WebUI Graphical Launcher

Graphical application that runs the Python application `open-webui` and wraps the web interface in a single-window container implemented using the `pywebview` package.

## Architecture Overview

The application follows a modular architecture with clear separation of concerns:

- **UI Layer**: `pywebview`-based main window with menu bar
- **Process Management Layer**: Subprocess handling for `open-webui serve`
- **Health Check Layer**: HTTP-based service availability monitoring
- **State Management Layer**: Application state coordination between components

### Key Design Decisions

- **Separation of Concerns**: Runner, UI, and coordination logic are separated
- **Observer Pattern**: State changes and output updates use callback subscriptions
- **Thread Safety**: Runner uses threading for non-blocking operations and state management
- **Fail-Safe**: Health checker with timeouts
- **Graceful Shutdown**: Proper cleanup sequence ensures no orphaned processes
- **Minimalist UI**: Status pages are simple HTML, no complex UI framework needed
- **No Persistence**: No configuration management from application for simplicity, configuration provided via env variables

### Guidelines

- **Error Handling**: Every component should log errors using the logger package
- **Resource Cleanup**: Ensure all threads are joined and processes terminated on exit
- **Logging**: Use appropriate log levels (DEBUG for detailed flow, INFO for major events, ERROR for failures)

### Dependencies

Additional standard library modules used:

- `subprocess` - Process management
- `threading` - Background tasks
- `enum` - State enumeration
- `os` - Environment variables
- `sys` - Exit codes
- `time` - Delays and timeouts
- `requests` - HTTP health checks
