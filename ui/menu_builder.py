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
            List of menu item dictionaries compatible with pywebview
        """
        menu = [
            {
                "label": "File",
                "items": [
                    {"label": "Exit", "action": callbacks.get("exit", lambda: None)}
                ],
            },
            {
                "label": "Control",
                "items": [
                    {"label": "Start", "action": callbacks.get("start", lambda: None)},
                    {"label": "Stop", "action": callbacks.get("stop", lambda: None)},
                    {
                        "label": "Restart",
                        "action": callbacks.get("restart", lambda: None),
                    },
                    {
                        "label": "-"  # Separator
                    },
                    {
                        "label": "Toggle Console",
                        "action": callbacks.get("toggle_console", lambda: None),
                    },
                ],
            },
            {
                "label": "Help",
                "items": [
                    {"label": "About", "action": callbacks.get("about", lambda: None)}
                ],
            },
        ]

        return menu

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
