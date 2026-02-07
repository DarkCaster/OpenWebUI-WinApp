from ui.main_window import MainWindow
from ui.status_pages import StatusPage
from ui.system_tray import SystemTray
from .process_state import ProcessState
from .openwebui_runner import OpenWebUIRunner
from .config import (
    PORT,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    SYSTEM_TRAY_TITLE,
    SHUTDOWN_TIMEOUT,
)
from .logger import get_logger


class AppController:
    """
    Coordinate between UI and runner components, manage application lifecycle.

    Central coordinator for the application that manages dependencies between
    components and handles application startup and shutdown.
    """

    def __init__(self):
        """
        Initialize the application controller.
        """
        self.logger = get_logger(__name__)
        self.runner: OpenWebUIRunner = None
        self.window: MainWindow = None
        self.system_tray: SystemTray = None
        self.is_exiting = False

        self.logger.info("AppController initialized")

    def initialize(self) -> None:
        """
        Set up all components.

        Creates runner and window instances and wires up callbacks.
        """
        self.logger.info("Initializing application components")

        # Create runner instance
        self.runner = OpenWebUIRunner(port=PORT)

        # Create main window instance with initial starting page
        # (since auto-start happens immediately after window is ready)
        self.window = MainWindow(
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            runner=self.runner,
            initial_html=StatusPage.starting_page(),
            on_ready_callback=self._on_window_ready,
            on_closing_callback=self._on_window_closing,
            minimize_to_tray=True,
        )

        # Initialize window
        self.window.initialize()

        # Create system tray instance
        self.system_tray = SystemTray(
            title=SYSTEM_TRAY_TITLE,
            on_open=self._on_tray_open,
            on_exit=self._on_tray_exit,
        )

        # Wire up callbacks
        self.runner.subscribe_to_state_change(self.on_runner_state_changed)
        self.runner.subscribe_to_output(self.on_runner_output)

        self.logger.info("Application components initialized")

    def start_application(self) -> None:
        """
        Begin application lifecycle.

        Shows the main window (blocking call). Auto-start happens after window is ready.
        """
        self.logger.info("Starting application")

        # Start system tray before showing window
        if self.system_tray:
            self.system_tray.start()

        # Show window (blocking call)
        # Auto-start will be triggered by _on_window_ready callback
        # When window closes, this call will return
        self.window.show()

        # Window has been closed, log this event
        self.logger.info("Main window closed")

    def _on_window_ready(self) -> None:
        """
        Callback executed after the window is ready.

        Auto-starts the Open WebUI runner.
        """
        self.logger.info("Window is ready, auto-starting Open WebUI")
        try:
            self.runner.start()
        except Exception as e:
            self.logger.error(f"Failed to auto-start Open WebUI: {e}")
            self.window.load_html(StatusPage.error_page(f"Failed to start: {str(e)}"))

    def _on_window_closing(self) -> None:
        """
        Callback executed when the window is being closed.

        Ensures runner is stopped before window closes.
        Only stops runner if this is a real exit (not minimize to tray).
        """
        self.logger.info("Window closing event received")

        # Check if this is a real exit or just minimize to tray
        if self.window and not self.window.should_exit:
            self.logger.info("Window minimized to tray, runner continues")
            return

        # This is a real exit, stop the runner
        self.is_exiting = True

        if self.runner:
            state = self.runner.get_state()
            if state in (ProcessState.RUNNING, ProcessState.STARTING):
                self.logger.info("Stopping runner due to window closing")
                try:
                    # Use a shorter timeout for window close to avoid hanging
                    self.runner.stop(timeout=SHUTDOWN_TIMEOUT)
                except Exception as e:
                    self.logger.error(f"Error stopping runner during window close: {e}")

    def _on_tray_open(self) -> None:
        """
        Callback executed when user clicks "Open" in system tray or left-clicks icon.

        Toggles window visibility (shows if hidden, hides if visible).
        """
        self.logger.info("Tray open action received")
        if self.is_exiting:
            return

        if self.window:
            if self.window.is_visible():
                self.logger.info("Window is visible, hiding to tray")
                self.window.hide()
            else:
                self.logger.info("Window is hidden, restoring from tray")
                self.window.restore()

    def _on_tray_exit(self) -> None:
        """
        Callback executed when user clicks "Exit" in system tray.

        Stops runner, stops system tray, and exits application.
        """
        self.logger.info("Tray exit action received")

        if self.is_exiting:
            return
        self.is_exiting = True

        # Destroy window, this will trigger full app shutdown
        if self.window:
            self.window.destroy()

    def shutdown(self) -> None:
        """
        Graceful application shutdown.

        Stops the runner, system tray, and performs cleanup.
        """
        self.logger.info("Shutting down application")

        self.is_exiting = True

        # Stop runner if running
        if self.runner:
            state = self.runner.get_state()
            if state in (ProcessState.RUNNING, ProcessState.STARTING):
                self.logger.info("Stopping runner during shutdown")
                try:
                    self.runner.stop(timeout=SHUTDOWN_TIMEOUT)
                except Exception as e:
                    self.logger.error(f"Error stopping runner during shutdown: {e}")

        # Stop system tray
        if self.system_tray:
            try:
                self.logger.info("Stopping system tray during shutdown")
                self.system_tray.stop()
            except Exception as e:
                self.logger.error(f"Error stopping system tray during shutdown: {e}")

        self.logger.info("Application shutdown complete")

    def on_runner_state_changed(
        self, old_state: ProcessState, new_state: ProcessState
    ) -> None:
        """
        Handle state transitions and update UI accordingly.

        Args:
            old_state: Previous process state
            new_state: New process state
        """
        self.logger.info(f"Handling state change: {old_state} -> {new_state}")

        # Load appropriate page based on new state
        if new_state == ProcessState.STOPPED:
            # Reset startup tracking flags
            if self.window:
                self.window.reset_startup_tracking()

            # Skip main content UI updates if console is visible
            if self.window and self.window.console_visible:
                self.logger.debug("Console visible, skipping state page update")
                return

            self.logger.debug("Loading stopped page")
            if self.window:
                self.window.load_html(StatusPage.stopped_page())

        elif new_state == ProcessState.STARTING:
            # Auto-open console to show startup messages
            if self.window:
                self.window.open_console_auto()

            # Load starting page in background (will be shown if console is toggled off)
            self.logger.debug("Loading starting page")
            if self.window:
                self.window.load_html(StatusPage.starting_page())

        elif new_state == ProcessState.RUNNING:
            self.logger.debug("Service is running")
            if self.window and self.runner:
                url = f"http://{self.runner.host}:{self.runner.port}"

                # Check if console should be auto-closed
                if self.window.should_auto_close_console():
                    # Auto-close console and load URL
                    self.logger.info("Auto-closing console and loading Open WebUI URL")
                    self.window.close_console_auto()
                    self.window.load_url(url)
                else:
                    # User manually controlled console, respect their choice
                    if not self.window.console_visible:
                        # Console is hidden, load URL
                        self.logger.debug("Loading Open WebUI URL")
                        self.window.load_url(url)
                    else:
                        # Console is visible by user choice, don't load URL yet
                        self.logger.debug(
                            "Console visible by user choice, not loading URL"
                        )

        elif new_state == ProcessState.STOPPING:
            # Skip main content UI updates if console is visible
            if self.window and self.window.console_visible:
                self.logger.debug("Console visible, skipping state page update")
                return

            self.logger.debug("Loading stopping page")
            if self.window:
                self.window.load_html(StatusPage.stopping_page())

        elif new_state == ProcessState.ERROR:
            # Reset startup tracking flags
            if self.window:
                self.window.reset_startup_tracking()

            # Skip main content UI updates if console is visible
            if self.window and self.window.console_visible:
                self.logger.debug("Console visible, skipping state page update")
                return

            self.logger.debug("Loading error page")
            if self.window:
                # Get recent output lines to include in error message
                error_message = "An error occurred while running Open WebUI."
                if self.runner:
                    last_lines = self.runner.get_output_lines(max_lines=10)
                    if last_lines:
                        error_message += "\n\nRecent output:\n" + "\n".join(last_lines)
                    else:
                        error_message += "\n\nNo output was captured from the process."
                error_message += "\n\nCheck the console for more details."
                self.window.load_html(StatusPage.error_page(error_message))

    def on_runner_output(self, line: str) -> None:
        """
        Handle new output from runner and update console view.

        Args:
            line: New output line from runner
        """
        self.logger.debug(f"Runner output: {line}")

        # Update console view if visible
        if self.window and self.window.console_visible:
            self.window.request_console_update()
