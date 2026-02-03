# Creating openwebui graphical launcher

## Application Development Plan

### Phase 1: Core Process Management

#### 1. `runner/__init__.py`

**Purpose**: Package initialization, exposes main runner interface.

**Exports**:

- `OpenWebUIRunner` class
- `ProcessState` enum

#### 2. `runner/process_state.py`

**Purpose**: Define process lifecycle states.

**Contents**:

- `ProcessState` enum with values:
  - `STOPPED` - Process is not running
  - `STARTING` - Process is launching, waiting for health check
  - `RUNNING` - Process is running and healthy
  - `STOPPING` - Process is being terminated
  - `ERROR` - Process encountered an error

#### 3. `runner/health_checker.py`

**Purpose**: Monitor open-webui service availability via HTTP requests.

**Class**: `HealthChecker`

- Performs HTTP GET requests to `http://127.0.0.1:<port>`
- Configurable timeout and retry logic
- Non-blocking health check execution using threading
- Methods:
  - `check_availability()` - Single health check attempt
  - `wait_until_ready()` - Blocks until service is available or timeout
  - `start_monitoring()` - Begin periodic health checks
  - `stop_monitoring()` - Stop periodic health checks

#### 4. `runner/openwebui_runner.py`

**Purpose**: Manage the `open-webui serve` subprocess lifecycle.

**Class**: `OpenWebUIRunner`

- Creates and manages subprocess running `open-webui serve --port <port>`
- Captures stdout/stderr from subprocess
- Integrates with `HealthChecker` for service availability
- Thread-safe state transitions
- Methods:
  - `start()` - Launch the open-webui process
  - `stop()` - Gracefully terminate the process
  - `restart()` - Stop and start the process
  - `get_state()` - Return current `ProcessState`
  - `get_output_lines()` - Return captured console output
  - `subscribe_to_output()` - Register callback for new output lines
  - `subscribe_to_state_change()` - Register callback for state changes

**Implementation notes**:

- Use `subprocess.Popen` with `stdout=PIPE, stderr=STDOUT`
- Use separate thread to read subprocess output to avoid blocking
- Implement graceful shutdown with timeout before force kill
- Port number read from `PORT` environment variable with fallback to 8080

### Phase 2: UI Layer - Status Pages

#### 5. `ui/__init__.py`

**Purpose**: Package initialization for UI components.

**Exports**:

- `MainWindow` class
- `StatusPage` class

#### 6. `ui/status_pages.py`

**Purpose**: Generate HTML content for various application states.

**Class**: `StatusPage`

- Static methods to generate HTML for different states:
  - `starting_page()` - "Starting Open WebUI..." with spinner
  - `stopping_page()` - "Stopping Open WebUI..." message
  - `stopped_page()` - "Open WebUI is stopped" with start button instructions
  - `error_page(message)` - Error display with details

**Implementation notes**:

- Simple HTML with inline CSS for styling
- Minimal, clean design

### Phase 3: UI Layer - Main Window

#### 7. `ui/console_view.py`

**Purpose**: Console output display component.

**Class**: `ConsoleView`

- Manages a scrollable console output display
- Methods:
  - `generate_html(lines)` - Convert output lines to HTML
  - `update_content(lines)` - Update displayed content
  - `clear()` - Clear console content

**Implementation notes**:

- Auto-scroll to bottom on new content
- Color coding for different log levels (optional)
- Maximum line limit to prevent memory issues (e.g., keep last 1000 lines)

#### 8. `ui/menu_builder.py`

**Purpose**: Create menu bar structure for the main window.

**Class**: `MenuBuilder`

- Builds menu structure for `pywebview`
- Methods:
  - `build_menu(callbacks)` - Create menu dictionary with callback bindings

**Menu structure**:

- **File**
  - Exit
- **Control**
  - Start
  - Stop
  - Restart
  - (Separator)
  - Toggle Console (show/hide)
- **Help**
  - About

**Implementation notes**:

- Menu items should enable/disable based on current process state
- State-aware: e.g., "Start" disabled when running, "Stop" disabled when stopped

#### 9. `ui/main_window.py`

**Purpose**: Main application window using `pywebview`.

**Class**: `MainWindow`

- Creates and manages the main `pywebview` window
- Coordinates between UI and runner components
- Handles menu callbacks
- Methods:
  - `initialize()` - Create window and set up components
  - `show()` - Display the window
  - `load_url(url)` - Load specific URL in window
  - `load_html(html)` - Load HTML content in window
  - `toggle_console()` - Show/hide console panel
  - `handle_start()` - Menu callback for start action
  - `handle_stop()` - Menu callback for stop action
  - `handle_restart()` - Menu callback for restart action
  - `handle_exit()` - Menu callback for exit action

**Implementation notes**:

- Window size: 1200x800 pixels (configurable)
- Window title: "Open WebUI Launcher"
- Console panel: docked at bottom, ~200px height when visible
- Main content area: displays either status pages or open-webui URL
- Subscribe to runner state changes to update UI automatically
- Subscribe to runner output to update console view

### Phase 4: Application Coordination

#### 10. `app_controller.py`

**Purpose**: Coordinate between UI and runner components, manage application lifecycle.

**Class**: `AppController`

- Central coordinator for the application
- Manages dependencies between components
- Handles application startup and shutdown
- Methods:
  - `initialize()` - Set up all components
  - `start_application()` - Begin application lifecycle
  - `shutdown()` - Graceful application shutdown
  - `on_runner_state_changed(old_state, new_state)` - Handle state transitions
  - `on_runner_output(line)` - Handle new output from runner

**Responsibilities**:

- Create `OpenWebUIRunner` instance
- Create `MainWindow` instance
- Wire up callbacks between components
- Implement state-based UI updates:
  - `STOPPED` → show stopped page
  - `STARTING` → show starting page
  - `RUNNING` → load `http://127.0.0.1:<port>`
  - `STOPPING` → show stopping page
  - `ERROR` → show error page
- Auto-start open-webui on application launch
- Clean up resources on exit

#### 11. `config.py`

**Purpose**: Application configuration and constants.

**Contents**:

- `PORT` - Port number from environment variable or default 8080
- `HEALTH_CHECK_TIMEOUT` - Maximum time to wait for service (e.g., 60 seconds)
- `SHUTDOWN_TIMEOUT` - Time to wait for graceful shutdown (e.g., 10 seconds)
- `MAX_CONSOLE_LINES` - Maximum console output lines to keep (e.g., 1000)
- `WINDOW_WIDTH` - Default window width (e.g., 1200)
- `WINDOW_HEIGHT` - Default window height (e.g., 800)

**Implementation notes**:

- Use `os.getenv()` for environment variables
- Provide sensible defaults
- All values should be module-level constants

### Phase 5: Application Entry Point

#### 12. `main.py` (update)

**Purpose**: Application entry point - instantiate and run the application.

**Responsibilities**:

- Set up logging using existing `logger` package
- Create `AppController` instance
- Initialize and start the application
- Handle top-level exceptions
- Ensure cleanup on exit

**Implementation flow**:

1. Call `setup_logging()` from logger package
2. Get logger instance
3. Log application startup
4. Read PORT from environment
5. Create and initialize `AppController`
6. Start application (blocking call)
7. Handle keyboard interrupt (Ctrl+C)
8. Ensure proper shutdown on exit
9. Exit with appropriate status code
