import threading
import time
import webview
from typing import Optional, Callable, List
from .menu_builder import MenuBuilder
from .console_view import ConsoleView
from .status_pages import StatusPage
from app.process_state import ProcessState
from app.openwebui_runner import OpenWebUIRunner
from app.config import WEB_STORAGE, OPEN_EXTERNAL_LINKS_IN_BROWSER, TEST_PAGE
from app.logger import get_logger


class MainWindow:
    """
    Main application window using pywebview.

    Creates and manages the main pywebview window, coordinates between
    UI and runner components, and handles menu callbacks.
    """

    def __init__(
        self,
        width: int = 1200,
        height: int = 800,
        runner: Optional[OpenWebUIRunner] = None,
        initial_html: Optional[str] = None,
        on_ready_callback: Optional[Callable[[], None]] = None,
        on_closing_callback: Optional[Callable[[], None]] = None,
        minimize_to_tray: bool = True,
    ):
        """
        Initialize the main window.

        Args:
            width: Window width in pixels
            height: Window height in pixels
            runner: Reference to OpenWebUIRunner instance
            initial_html: Initial HTML content to display when window is created
            on_ready_callback: Callback function to execute after window is ready
            on_closing_callback: Callback function to execute when window is closing
            minimize_to_tray: If True, closing window hides to tray instead of exiting
        """
        self.width = width
        self.height = height
        self.runner = runner
        self.initial_html = initial_html
        self.on_ready_callback = on_ready_callback
        self.on_closing_callback = on_closing_callback
        self.minimize_to_tray = minimize_to_tray

        self.window: Optional[webview.Window] = None
        self.console_view = ConsoleView(max_lines=1000)
        self.console_visible = False
        self.auto_scroll_enabled = True
        self.window_ready = False
        self.is_hidden = False
        self.should_exit = False

        # Console auto-open tracking for startup
        self.console_auto_opened = False
        self.console_manually_toggled_during_startup = False

        # Console update throttling
        self._console_update_requested = False
        self._console_update_lock = threading.Lock()
        self._console_update_thread: Optional[threading.Thread] = None
        self._console_update_interval = 0.5  # seconds

        # Console incremental update tracking
        self._console_initialized = False
        self._last_console_line_count = 0

        self.logger = get_logger(__name__)
        self.logger.info(f"MainWindow initialized ({width}x{height})")

    def initialize(self) -> None:
        """
        Create window and set up components.
        """
        self.logger.info("Initializing main window")

        # Build menu with callbacks
        menu = MenuBuilder.build_menu(
            {
                "start": self.handle_start,
                "stop": self.handle_stop,
                "restart": self.handle_restart,
                "toggle_console": self.handle_toggle_console,
                "toggle_auto_scroll": self.handle_toggle_auto_scroll,
                "exit": self.handle_exit,
                "home": self.handle_home,
                "back": self.handle_back,
                "test_page": self.handle_test_page,
            },
            test_page_url=TEST_PAGE,
        )

        webview.settings["ALLOW_DOWNLOADS"] = True
        webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = (
            OPEN_EXTERNAL_LINKS_IN_BROWSER
        )

        # Create the main window with initial content
        if self.initial_html:
            self.window = webview.create_window(
                title="Open WebUI Launcher",
                html=self.initial_html,
                width=self.width,
                height=self.height,
                resizable=True,
                fullscreen=False,
                min_size=(800, 600),
                menu=menu,
            )
        else:
            self.window = webview.create_window(
                title="Open WebUI Launcher",
                url="",
                width=self.width,
                height=self.height,
                resizable=True,
                fullscreen=False,
                min_size=(800, 600),
                menu=menu,
            )

        # Register window closing event handler
        self.window.events.closing += self._on_window_closing_event

        # Note: pywebview does not provide a minimize event handler
        # Therefore, the minimize button cannot be intercepted to hide to tray
        # Only the close button can trigger hide-to-tray behavior

        self.logger.info("Main window created")

    def show(self) -> None:
        """
        Display the window (blocking call).
        """
        if not self.window:
            self.logger.error("Cannot show window: not initialized")
            return

        self.logger.info("Starting pywebview")

        # Window is being shown, mark as visible
        self.is_hidden = False

        # If there's a ready callback, wrap it to set window_ready flag
        if self.on_ready_callback:

            def wrapped_callback():
                self.window_ready = True
                self.logger.debug("Window ready flag set")
                self.on_ready_callback()

            webview.start(
                wrapped_callback, storage_path=WEB_STORAGE, private_mode=False
            )
        else:

            def ready_callback():
                self.window_ready = True
                self.logger.debug("Window ready flag set")

            webview.start(ready_callback, storage_path=WEB_STORAGE, private_mode=False)

    def load_url(self, url: str) -> None:
        """
        Load specific URL in window.

        Args:
            url: URL to load
        """
        if not self.window:
            self.logger.error("Cannot load URL: window not initialized")
            return

        if not self.window_ready:
            self.logger.warning("Attempting to load URL before window is ready")

        self.logger.info(f"Loading URL: {url}")
        self.window.load_url(url)

    def load_html(self, html: str) -> None:
        """
        Load HTML content in window.

        Args:
            html: HTML content to load
        """
        if not self.window:
            self.logger.error("Cannot load HTML: window not initialized")
            return

        if not self.window_ready:
            self.logger.warning("Attempting to load HTML before window is ready")

        self.logger.debug("Loading HTML content")
        self.window.load_html(html)

    def open_console_auto(self) -> None:
        """
        Automatically open console (used during startup).

        Sets flags to track that console was auto-opened.
        """
        self.logger.info("Auto-opening console for startup")
        self.console_visible = True
        self.console_auto_opened = True
        self.console_manually_toggled_during_startup = False

        # Reset console state for fresh initialization
        self._console_initialized = False
        self._last_console_line_count = 0

        # Update console with current output
        if self.runner:
            lines = self.runner.get_output_lines()
            self._perform_console_update(lines)

        # Start console update thread for periodic updates
        self._start_console_update_thread()

    def close_console_auto(self) -> None:
        """
        Automatically close console (used when startup completes).

        Resets auto-open tracking flags.
        """
        self.logger.info("Auto-closing console after startup")
        self.console_visible = False
        self.console_auto_opened = False
        self.console_manually_toggled_during_startup = False

        # Reset console state
        self._console_initialized = False
        self._last_console_line_count = 0

        # Stop console update thread
        self._stop_console_update_thread()

    def reset_startup_tracking(self) -> None:
        """
        Reset console auto-open tracking flags.

        Called when transitioning to STOPPED or ERROR states.
        """
        self.logger.debug("Resetting startup tracking flags")
        self.console_auto_opened = False
        self.console_manually_toggled_during_startup = False

    def should_auto_close_console(self) -> bool:
        """
        Determine if console should be automatically closed.

        Returns:
            True if console was auto-opened and user didn't manually toggle it
        """
        should_close = (
            self.console_auto_opened
            and not self.console_manually_toggled_during_startup
        )
        self.logger.debug(
            f"Should auto-close console: {should_close} "
            f"(auto_opened={self.console_auto_opened}, "
            f"manually_toggled={self.console_manually_toggled_during_startup})"
        )
        return should_close

    def toggle_console(self) -> None:
        """
        Show/hide console panel.
        """
        # Check if we're in STARTING state and track manual toggle
        if self.runner:
            state = self.runner.get_state()
            if state == ProcessState.STARTING:
                self.logger.debug("Console toggled manually during startup")
                self.console_manually_toggled_during_startup = True
                self.console_auto_opened = False

        self.console_visible = not self.console_visible

        if self.console_visible:
            self.logger.info("Console panel shown")
            # Reset console state for fresh initialization
            self._console_initialized = False
            self._last_console_line_count = 0
            # Update console with current output
            if self.runner:
                lines = self.runner.get_output_lines()
                self._perform_console_update(lines)
            # Start console update thread for periodic updates
            self._start_console_update_thread()
        else:
            self.logger.info("Console panel hidden")
            # Reset console state
            self._console_initialized = False
            self._last_console_line_count = 0
            # Stop console update thread
            self._stop_console_update_thread()
            # Reload current state page or URL
            if self.runner:
                state = self.runner.get_state()
                self._load_state_page(state)

    def request_console_update(self) -> None:
        """
        Request a console update (will be throttled).

        This method can be called frequently but actual updates
        will be batched according to the update interval.
        """
        with self._console_update_lock:
            self._console_update_requested = True

    def update_console(self, lines: List[str]) -> None:
        """
        Update console view content.

        Args:
            lines: List of output lines to display
        """
        if not self.console_visible:
            return

        self._perform_console_update(lines)

    def _perform_console_update(self, lines: List[str]) -> None:
        """
        Actually perform the console HTML update.

        Uses incremental updates after initial load to avoid disrupting scroll position.

        Args:
            lines: List of output lines to display
        """
        current_line_count = len(lines)

        # Check if we need to do a full reload
        # (first time, or line count decreased indicating buffer was trimmed)
        if (
            not self._console_initialized
            or current_line_count < self._last_console_line_count
        ):
            self.logger.debug("Performing full console initialization")
            self.console_view.update_content(lines)
            html = self.console_view.generate_initial_html(
                auto_scroll=self.auto_scroll_enabled
            )
            self.load_html(html)
            self._console_initialized = True
            self._last_console_line_count = current_line_count
        else:
            # Incremental update: append only new lines
            new_line_count = current_line_count - self._last_console_line_count

            if new_line_count > 0:
                # Extract new lines
                new_lines = lines[-new_line_count:]

                # Generate JavaScript to append new lines
                script = self.console_view.generate_append_script(
                    new_lines, self.auto_scroll_enabled
                )

                if script and self.window:
                    try:
                        self.window.evaluate_js(script)
                        self._last_console_line_count = current_line_count
                        self.logger.debug(
                            f"Appended {new_line_count} new lines to console"
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Failed to evaluate JavaScript for console update: {e}"
                        )
                        # Fall back to full reload on error
                        self._console_initialized = False
                        self._perform_console_update(lines)
            # If no new lines, do nothing (no need to update)

    def _start_console_update_thread(self) -> None:
        """
        Start the background thread for throttled console updates.
        """
        if self._console_update_thread and self._console_update_thread.is_alive():
            return

        self._console_update_thread = threading.Thread(
            target=self._console_update_worker, daemon=True, name="ConsoleUpdateWorker"
        )
        self._console_update_thread.start()
        self.logger.debug("Console update thread started")

    def _stop_console_update_thread(self) -> None:
        """
        Stop the background thread for throttled console updates.
        """
        # The thread will exit naturally when console_visible becomes False
        if self._console_update_thread:
            self.logger.debug("Waiting for console update thread to stop")
            self._console_update_thread.join(timeout=2)

    def _console_update_worker(self) -> None:
        """
        Background worker that performs throttled console updates.
        """
        self.logger.debug("Console update worker started")

        while self.console_visible:
            # Check if update was requested
            update_needed = False
            with self._console_update_lock:
                if self._console_update_requested:
                    update_needed = True
                    self._console_update_requested = False

            # Perform update if needed
            if update_needed and self.runner:
                lines = self.runner.get_output_lines()
                self._perform_console_update(lines)

            # Sleep for the update interval
            time.sleep(self._console_update_interval)

        self.logger.debug("Console update worker stopped")

    def handle_start(self) -> None:
        """
        Menu callback for start action.
        """
        self.logger.info("Start action triggered from menu")

        if not self.runner:
            self.logger.error("No runner available")
            return

        try:
            success = self.runner.start()
            if not success:
                self.logger.warning("Failed to start runner")
        except Exception as e:
            self.logger.error(f"Error starting runner: {e}")

    def handle_stop(self) -> None:
        """
        Menu callback for stop action.
        """
        self.logger.info("Stop action triggered from menu")

        if not self.runner:
            self.logger.error("No runner available")
            return

        try:
            success = self.runner.stop()
            if not success:
                self.logger.warning("Failed to stop runner")
        except Exception as e:
            self.logger.error(f"Error stopping runner: {e}")

    def handle_restart(self) -> None:
        """
        Menu callback for restart action.
        """
        self.logger.info("Restart action triggered from menu")

        if not self.runner:
            self.logger.error("No runner available")
            return

        try:
            success = self.runner.restart()
            if not success:
                self.logger.warning("Failed to restart runner")
        except Exception as e:
            self.logger.error(f"Error restarting runner: {e}")

    def handle_toggle_console(self) -> None:
        """
        Menu callback for toggle console action.
        """
        self.logger.info("Toggle console action triggered from menu")
        self.toggle_console()

    def handle_toggle_auto_scroll(self) -> None:
        """
        Menu callback for toggle auto-scroll action.
        """
        self.auto_scroll_enabled = not self.auto_scroll_enabled
        self.logger.info(
            f"Auto-scroll {'enabled' if self.auto_scroll_enabled else 'disabled'}"
        )

        # If console is visible and auto-scroll was just enabled, scroll to bottom
        if self.console_visible and self.auto_scroll_enabled and self.window:
            try:
                self.window.evaluate_js("scrollToBottom();")
            except Exception as e:
                self.logger.error(f"Failed to scroll to bottom: {e}")

    def handle_exit(self) -> None:
        """
        Menu callback for exit action.
        """
        self.logger.info("Exit action triggered from menu")

        # Set flag to indicate this is a real exit (not minimize to tray)
        self.should_exit = True

        # Trigger the closing callback (which will stop the runner)
        if self.on_closing_callback:
            self.on_closing_callback()

        # Destroy the window
        if self.window:
            self.window.destroy()

    def handle_home(self) -> None:
        """
        Menu callback for home action (navigate to service home page).
        """
        self.logger.info("Home action triggered from menu")

        if not self.runner:
            self.logger.error("No runner available")
            return

        state = self.runner.get_state()

        # Only perform navigation if service is running
        if state == ProcessState.RUNNING:
            url = f"http://{self.runner.host}:{self.runner.port}"
            self.logger.info(f"Navigating to home: {url}")
            self.load_url(url)
        else:
            self.logger.warning(
                f"Home navigation ignored - service not running (state: {state})"
            )

    def handle_back(self) -> None:
        """
        Menu callback for back action (browser back navigation).
        """
        self.logger.info("Back action triggered from menu")

        if not self.runner:
            self.logger.error("No runner available")
            return

        state = self.runner.get_state()

        # Only perform navigation if service is running
        if state == ProcessState.RUNNING:
            if self.window:
                try:
                    self.logger.info("Executing browser back navigation")
                    self.window.evaluate_js("history.back();")
                except Exception as e:
                    self.logger.error(f"Failed to execute back navigation: {e}")
        else:
            self.logger.warning(
                f"Back navigation ignored - service not running (state: {state})"
            )

    def handle_test_page(self) -> None:
        """
        Menu callback for test page action (navigate to test page URL).
        """
        self.logger.info(
            f"Test Page action triggered from menu - navigating to {TEST_PAGE}"
        )
        self.load_url(TEST_PAGE)

    def _on_window_closing_event(self) -> bool:
        """
        Event handler called when window is being closed.

        Returns:
            True to allow window close, False to cancel
        """
        self.logger.info("Window closing event triggered")

        # Check if we should minimize to tray instead of closing
        if self.minimize_to_tray and not self.should_exit:
            self.logger.info("Minimizing to system tray instead of closing")
            self.hide()
            # Return False to cancel the close event
            return False

        # This is a real exit, call the closing callback
        self.logger.info("Proceeding with window close")
        if self.on_closing_callback:
            self.on_closing_callback()

        return True

    def hide(self) -> None:
        """
        Hide window to system tray.
        """
        if not self.window:
            self.logger.error("Cannot hide window: not initialized")
            return

        self.logger.info("Hiding window to system tray")
        self.is_hidden = True
        self.window.hide()

    def restore(self) -> None:
        """
        Restore window from system tray.
        """
        if not self.window:
            self.logger.error("Cannot restore window: not initialized")
            return

        self.logger.info("Restoring window from system tray")
        self.is_hidden = False
        self.window.show()

    def is_visible(self) -> bool:
        """
        Check if window is currently visible.

        Returns:
            True if window is visible, False if hidden
        """
        return not self.is_hidden

    def destroy(self) -> None:
        """
        Destroy the window.
        """
        if not self.window:
            self.logger.error("Cannot destroy window: not initialized")
            return

        self.logger.info("Destroying window")
        self.should_exit = True
        self.window.destroy()

    def _load_state_page(self, state: ProcessState) -> None:
        """
        Load appropriate page based on process state.

        Args:
            state: Current process state
        """
        if state == ProcessState.STOPPED:
            self.load_html(StatusPage.stopped_page())
        elif state == ProcessState.STARTING:
            self.load_html(StatusPage.starting_page())
        elif state == ProcessState.STOPPING:
            self.load_html(StatusPage.stopping_page())
        elif state == ProcessState.ERROR:
            self.load_html(
                StatusPage.error_page("An error occurred while running Open WebUI")
            )
        elif state == ProcessState.RUNNING:
            # This should be handled by loading the actual URL
            if self.runner:
                url = f"http://{self.runner.host}:{self.runner.port}"
                self.load_url(url)
