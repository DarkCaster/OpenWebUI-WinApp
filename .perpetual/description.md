# Open WebUI Graphical Launcher

Graphical application that runs the Python web-application `open-webui` and wraps the web interface in a single-window container implemented using the `pywebview` package.

## Architecture Overview

The application follows a simple modular architecture:

- **UI Layer**: `pywebview`-based main window with menu bar
- **Management Layer**: Application state coordination between components, subprocess handling for `open-webui serve`

### Key Design Decisions

- **Separation of Concerns**: UI and application coordination logic are separated
- **Observer Pattern**: State changes and output updates use callback subscriptions
- **Thread Safety**: Using threading for non-blocking operations and state management
- **Minimalist UI**: Status pages are simple HTML, no complex UI framework needed
- **No Persistence**: No configuration editing and saving from application for simplicity, configuration provided via env variables

### Guidelines

- **Error Handling**: Every component should log errors using the logger package
- **Resource Cleanup**: Ensure all threads are joined and processes terminated on exit
- **Logging**: Use appropriate log levels (DEBUG for detailed flow, INFO for major events, ERROR for failures)
