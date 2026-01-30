import webview
from typing import Optional, Callable
from logger import get_logger
from .menu_builder import MenuBuilder
from .console_view import ConsoleView
from .status_pages import StatusPage
from runner import ProcessState, OpenWebUIRunner


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
        console_height: int = 200,
        runner: Optional[OpenWebUIRunner] = None,
        initial_html: Optional[str] = None,
        on_ready_callback: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize the main window.

        Args:
            width: Window width in pixels
            height: Window height in pixels
            console_height: Console panel height when visible
            runner: Reference to OpenWebUIRunner instance
            initial_html: Initial HTML content to display when window is created
            on_ready_callback: Callback function to execute after window is ready
        """
        self.width = width
        self.height = height
        self.console_height = console_height
        self.runner = runner
        self.initial_html = initial_html
        self.on_ready_callback = on_ready_callback

        self.window: Optional[webview.Window] = None
        self.console_view = ConsoleView(max_lines=1000)
        self.console_visible = False
        self.window_ready = False

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
                "about": self.handle_about,
                "exit": self.handle_exit,
            }
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

        self.logger.info("Main window created")

    def show(self) -> None:
        """
        Display the window (blocking call).
        """
        if not self.window:
            self.logger.error("Cannot show window: not initialized")
            return

        self.logger.info("Starting pywebview")
        
        # If there's a ready callback, wrap it to set window_ready flag
        if self.on_ready_callback:
            def wrapped_callback():
                self.window_ready = True
                self.logger.debug("Window ready flag set")
                self.on_ready_callback()
            webview.start(wrapped_callback)
        else:
            def ready_callback():
                self.window_ready = True
                self.logger.debug("Window ready flag set")
            webview.start(ready_callback)

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

    def toggle_console(self) -> None:
        """
        Show/hide console panel.
        """
        self.console_visible = not self.console_visible

        if self.console_visible:
            self.logger.info("Console panel shown")
            # Update console with current output
            if self.runner:
                lines = self.runner.get_output_lines()
                self.update_console(lines)
        else:
            self.logger.info("Console panel hidden")
            # Reload current state page or URL
            if self.runner:
                state = self.runner.get_state()
                self._load_state_page(state)

    def update_console(self, lines: list) -> None:
        """
        Update console view content.

        Args:
            lines: List of output lines to display
        """
        if not self.console_visible:
            return

        self.console_view.update_content(lines)
        html = self.console_view.generate_html(lines)
        self.load_html(html)

    def update_menu_state(self, process_state: ProcessState) -> None:
        """
        Enable/disable menu items based on process state.

        Note: pywebview doesn't support dynamic menu state updates,
        so this is a placeholder for potential future implementation.

        Args:
            process_state: Current process state
        """
        menu_state = MenuBuilder.get_menu_state(process_state)
        self.logger.debug(f"Menu state for {process_state}: {menu_state}")
        # pywebview limitation: cannot dynamically update menu item states
        # This would require rebuilding the entire menu structure

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

    def handle_about(self) -> None:
        """
        Menu callback for about action.
        """
        self.logger.info("About dialog requested")

        about_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>About</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    color: #fff;
                }
                .about-box {
                    background: rgba(255, 255, 255, 0.95);
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
                    text-align: center;
                    color: #333;
                }
                h1 {
                    margin: 0 0 20px 0;
                    color: #667eea;
                }
                p {
                    margin: 10px 0;
                    line-height: 1.6;
                }
            </style>
        </head>
        <body>
            <div class="about-box">
                <h1>Open WebUI Launcher</h1>
                <p><strong>Version:</strong> 1.0.0</p>
                <p>A graphical launcher for Open WebUI</p>
                <p>Wraps the web interface in a single-window container</p>
                <p style="margin-top: 20px; font-size: 0.9em; color: #666;">
                    Use Control menu to start, stop, or restart the service
                </p>
            </div>
        </body>
        </html>
        """

        # Create a temporary window for about dialog
        webview.create_window(
            title="About Open WebUI Launcher",
            html=about_html,
            width=400,
            height=300,
            resizable=False,
        )

    def handle_exit(self) -> None:
        """
        Menu callback for exit action.
        """
        self.logger.info("Exit action triggered from menu")

        # Stop runner if running
        if self.runner:
            state = self.runner.get_state()
            if state in (ProcessState.RUNNING, ProcessState.STARTING):
                self.logger.info("Stopping runner before exit")
                self.runner.stop()

        # Destroy the window
        if self.window:
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
                url = f"http://127.0.0.1:{self.runner.port}"
                self.load_url(url)
