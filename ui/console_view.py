from typing import List
from logger import get_logger


class ConsoleView:
    """
    Console output display component.

    Manages a scrollable console output display with automatic
    line limiting and HTML generation for display in the UI.
    """

    def __init__(self, max_lines: int = 1000):
        """
        Initialize the console view.

        Args:
            max_lines: Maximum number of lines to keep in buffer
        """
        self.max_lines = max_lines
        self._lines: List[str] = []
        self.logger = get_logger(__name__)

    def generate_html(self, lines: List[str]) -> str:
        """
        Convert list of output lines to styled HTML.

        Args:
            lines: List of console output lines

        Returns:
            HTML string with styled console output
        """
        # Escape HTML special characters in lines
        escaped_lines = []
        for line in lines:
            escaped_line = (
                line.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#x27;")
            )
            escaped_lines.append(escaped_line)

        # Join lines with HTML line breaks
        content = "<br>".join(escaped_lines) if escaped_lines else "No output yet..."

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Console Output</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Courier New', Consolas, monospace;
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    padding: 12px;
                    font-size: 13px;
                    line-height: 1.5;
                    overflow-y: auto;
                }}
                
                .console-content {{
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }}
                
                /* Ensure auto-scroll to bottom */
                html {{
                    scroll-behavior: smooth;
                }}
            </style>
            <script>
                // Auto-scroll to bottom when content loads
                window.addEventListener('load', function() {{
                    window.scrollTo(0, document.body.scrollHeight);
                }});
            </script>
        </head>
        <body>
            <div class="console-content">{content}</div>
        </body>
        </html>
        """

    def update_content(self, lines: List[str]) -> None:
        """
        Update internal line buffer with new lines.

        Respects max_lines limit by keeping only the most recent lines.

        Args:
            lines: List of output lines to store
        """
        self._lines = lines

        # Trim to max_lines if exceeded
        if len(self._lines) > self.max_lines:
            removed_count = len(self._lines) - self.max_lines
            self._lines = self._lines[-self.max_lines :]
            self.logger.debug(f"Trimmed {removed_count} lines from console buffer")

    def clear(self) -> None:
        """
        Clear the line buffer.
        """
        self._lines = []
        self.logger.debug("Console buffer cleared")

    def get_lines(self) -> List[str]:
        """
        Get current line buffer.

        Returns:
            List of stored output lines
        """
        return self._lines.copy()
