import threading
import pystray
from typing import Any, Optional, Callable
from PIL import Image, ImageDraw
from app.logger import get_logger


class SystemTray:
    """
    System tray icon manager.

    Creates and manages system tray icon with menu and click handlers.
    Runs in a background thread to avoid blocking the main UI.
    """

    def __init__(
        self,
        title: str = "Open WebUI Launcher",
        on_open: Optional[Callable[[], None]] = None,
        on_exit: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize the system tray icon.

        Args:
            title: Tooltip text for the tray icon
            on_open: Callback function when user clicks "Open" or left-clicks icon
            on_exit: Callback function when user clicks "Exit"
        """
        self.title = title
        self.on_open = on_open
        self.on_exit = on_exit

        self.icon: Optional[Any] = None
        self.tray_thread: Optional[threading.Thread] = None
        self.running = False
        self.lock = threading.Lock()

        self.logger = get_logger(__name__)
        self.logger.info("SystemTray initialized")

    def _create_icon_image(self) -> Image.Image:
        """
        Create a simple icon image for the system tray.

        Returns:
            PIL Image object
        """
        # Create a simple 64x64 icon with a colored circle
        width = 64
        height = 64
        color1 = (52, 152, 219)  # Blue
        color2 = (255, 255, 255)  # White

        # Create image with transparent background
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw a filled circle
        draw.ellipse([8, 8, width - 8, height - 8], fill=color1, outline=color2, width=2)

        # Draw inner circle/dot
        center = width // 2
        radius = 12
        draw.ellipse(
            [center - radius, center - radius, center + radius, center + radius],
            fill=color2,
        )

        return image

    def _create_menu(self) -> pystray.Menu:
        """
        Create the system tray menu.

        Returns:
            pystray.Menu object
        """
        return pystray.Menu(
            pystray.MenuItem("Open", self._handle_open, default=True),
            pystray.MenuItem("Exit", self._handle_exit),
        )

    def _handle_open(self, icon: Any, item: pystray.MenuItem) -> None:
        """
        Handle "Open" menu item or left-click on icon.

        Args:
            icon: The system tray icon
            item: The menu item (None for left-click)
        """
        self.logger.info("Tray: Open action triggered")
        if self.on_open:
            try:
                self.on_open()
            except Exception as e:
                self.logger.error(f"Error in on_open callback: {e}", exc_info=True)

    def _handle_exit(self, icon: Any, item: pystray.MenuItem) -> None:
        """
        Handle "Exit" menu item.

        Args:
            icon: The system tray icon
            item: The menu item
        """
        self.logger.info("Tray: Exit action triggered")
        if self.on_exit:
            try:
                self.on_exit()
            except Exception as e:
                self.logger.error(f"Error in on_exit callback: {e}", exc_info=True)

    def start(self) -> None:
        """
        Start the system tray icon in a background thread.
        """
        with self.lock:
            if self.running:
                self.logger.warning("System tray already running")
                return

            self.logger.info("Starting system tray")

            # Create icon image
            icon_image = self._create_icon_image()

            # Create menu
            menu = self._create_menu()

            # Create icon
            self.icon = pystray.Icon(
                name="open_webui_launcher",
                icon=icon_image,
                title=self.title,
                menu=menu,
            )

            # Set up left-click handler (same as "Open")
            # Note: pystray uses the default menu item for left-click,
            # which we already set in the menu creation

            # Start icon in background thread
            self.running = True
            self.tray_thread = threading.Thread(
                target=self._run_tray, daemon=False, name="SystemTrayThread"
            )
            self.tray_thread.start()

            self.logger.info("System tray started")

    def _run_tray(self) -> None:
        """
        Run the system tray icon (blocks until stopped).

        This method runs in a background thread.
        """
        try:
            self.logger.debug("System tray thread running")
            if self.icon:
                self.icon.run()
            self.logger.debug("System tray thread exited")
        except Exception as e:
            self.logger.error(f"Error in system tray thread: {e}", exc_info=True)
        finally:
            with self.lock:
                self.running = False

    def stop(self) -> None:
        """
        Stop the system tray icon and cleanup.
        """
        with self.lock:
            if not self.running:
                self.logger.warning("System tray not running")
                return

            self.logger.info("Stopping system tray")

            if self.icon:
                try:
                    self.icon.stop()
                except Exception as e:
                    self.logger.error(f"Error stopping tray icon: {e}", exc_info=True)

            self.running = False

        # Wait for thread to finish
        if self.tray_thread and self.tray_thread.is_alive():
            self.logger.debug("Waiting for tray thread to finish")
            self.tray_thread.join(timeout=5)
            if self.tray_thread.is_alive():
                self.logger.warning("Tray thread did not finish in time")

        self.logger.info("System tray stopped")

    def is_running(self) -> bool:
        """
        Check if the system tray is running.

        Returns:
            True if running, False otherwise
        """
        with self.lock:
            return self.running
