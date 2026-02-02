from webview.menu import Menu, MenuAction, MenuSeparator
from typing import Dict, Callable


class MenuBuilder:
    """
    Create menu bar structure for the main window.

    Builds menu structure compatible with pywebview and provides
    state-aware menu item enabling/disabling logic.
    """

    @staticmethod
    def build_menu(callbacks: Dict[str, Callable]) -> list:
        """
        Create menu dictionary with callback bindings.

        Args:
            callbacks: Dictionary mapping action names to callback functions.
                      Expected keys: 'start', 'stop', 'restart', 'toggle_console', 
                      'toggle_auto_scroll', 'exit', 'home', 'back'

        Returns:
            List of menu items compatible with pywebview (list of webview.Menu objects)
        """
        # File menu
        file_menu_items = [
            MenuAction('Exit', callbacks.get("exit", lambda: None))
        ]
        file_menu = Menu('File', file_menu_items)

        # Control menu
        control_menu_items = [
            MenuAction('Start', callbacks.get("start", lambda: None)),
            MenuAction('Stop', callbacks.get("stop", lambda: None)),
            MenuAction('Restart', callbacks.get("restart", lambda: None)),
            MenuSeparator(),
            MenuAction('Toggle Console', callbacks.get("toggle_console", lambda: None)),
            MenuAction('Toggle Auto-Scroll', callbacks.get("toggle_auto_scroll", lambda: None))
        ]
        control_menu = Menu('Control', control_menu_items)

        # Navigation menu
        navigation_menu_items = [
            MenuAction('Home', callbacks.get("home", lambda: None)),
            MenuAction('Back', callbacks.get("back", lambda: None))
        ]
        navigation_menu = Menu('Navigation', navigation_menu_items)

        return [file_menu, control_menu, navigation_menu]
