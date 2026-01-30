from webview.menu import Menu, MenuAction, MenuSeparator
from typing import Dict, Callable
from runner import ProcessState


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
                      Expected keys: 'start', 'stop', 'restart', 'toggle_console', 'about', 'exit'

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
            MenuAction('Toggle Console', callbacks.get("toggle_console", lambda: None))
        ]
        control_menu = Menu('Control', control_menu_items)

        # Help menu
        help_menu_items = [
            MenuAction('About', callbacks.get("about", lambda: None))
        ]
        help_menu = Menu('Help', help_menu_items)

        return [file_menu, control_menu, help_menu]

    @staticmethod
    def get_menu_state(process_state: ProcessState) -> Dict[str, bool]:
        """
        Get enabled/disabled states for menu items based on current ProcessState.

        Args:
            process_state: Current process state

        Returns:
            Dictionary mapping action names to enabled state (True=enabled, False=disabled)
        """
        # Default: all items disabled
        state = {
            "start": False,
            "stop": False,
            "restart": False,
            "toggle_console": True,  # Always enabled
            "about": True,  # Always enabled
            "exit": True,  # Always enabled
        }

        if process_state == ProcessState.STOPPED:
            # Only Start should be enabled
            state["start"] = True

        elif process_state == ProcessState.STARTING:
            # Only Stop should be enabled (to cancel startup)
            state["stop"] = True

        elif process_state == ProcessState.RUNNING:
            # Stop and Restart should be enabled
            state["stop"] = True
            state["restart"] = True

        elif process_state == ProcessState.STOPPING:
            # Nothing should be enabled during stopping (except always-enabled items)
            pass

        elif process_state == ProcessState.ERROR:
            # Start and Restart should be enabled to recover
            state["start"] = True
            state["restart"] = True

        return state
