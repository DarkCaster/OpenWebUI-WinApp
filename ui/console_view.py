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

    def generate_initial_html(self, auto_scroll: bool = True) -> str:
        """
        Generate complete initial HTML for console with JavaScript utilities.

        Args:
            auto_scroll: Whether to automatically scroll to bottom on page load

        Returns:
            HTML string with styled console output and JavaScript functions
        """
        # Escape HTML special characters in lines
        escaped_lines = []
        for line in self._lines:
            escaped_line = self._escape_html(line)
            escaped_lines.append(escaped_line)

        # Join lines with HTML line breaks
        content = "<br>".join(escaped_lines) if escaped_lines else "No output yet..."

        # Add on-load scroll script if auto-scroll is enabled
        onload_script = ""
        if auto_scroll:
            onload_script = """
            <script>
                // Scroll to bottom on initial page load
                window.addEventListener('load', function() {
                    scrollToBottom();
                });
            </script>
            """

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
            </style>
            <script>
                // Append new lines to console content
                function appendLines(lines, autoScroll) {{
                    var container = document.getElementById('console-content');
                    
                    // If content is placeholder, clear it first
                    if (container.innerHTML === 'No output yet...') {{
                        container.innerHTML = '';
                    }}
                    
                    // Add separator if there's existing content
                    if (container.innerHTML && lines.length > 0) {{
                        container.innerHTML += '<br>';
                    }}
                    
                    // Append new lines
                    container.innerHTML += lines.join('<br>');
                    
                    // Instantly scroll to bottom if auto-scroll enabled
                    if (autoScroll) {{
                        window.scrollTo(0, document.body.scrollHeight);
                    }}
                }}
                
                // Scroll to bottom instantly
                function scrollToBottom() {{
                    window.scrollTo(0, document.body.scrollHeight);
                }}
                
                // Get current scroll position
                function getScrollPosition() {{
                    return {{
                        scrollTop: window.pageYOffset || document.documentElement.scrollTop,
                        scrollHeight: document.body.scrollHeight,
                        clientHeight: window.innerHeight
                    }};
                }}
            </script>
        </head>
        <body>
            <div id="console-content" class="console-content">{content}</div>
            {onload_script}
        </body>
        </html>
        """

    def generate_append_script(self, new_lines: List[str], auto_scroll: bool) -> str:
        """
        Generate JavaScript code to append new lines to existing content.

        Args:
            new_lines: List of new lines to append
            auto_scroll: Whether to automatically scroll to bottom

        Returns:
            JavaScript code as string
        """
        if not new_lines:
            return ""

        # Escape HTML special characters and JavaScript strings
        escaped_lines = []
        for line in new_lines:
            # First escape HTML
            escaped_line = self._escape_html(line)
            # Then escape for JavaScript string (escape backslashes and quotes)
            escaped_line = escaped_line.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")
            escaped_lines.append(f"'{escaped_line}'")

        # Build JavaScript array
        lines_array = "[" + ", ".join(escaped_lines) + "]"
        auto_scroll_str = "true" if auto_scroll else "false"

        return f"appendLines({lines_array}, {auto_scroll_str});"

    def _escape_html(self, text: str) -> str:
        """
        Escape HTML special characters.

        Args:
            text: Text to escape

        Returns:
            Escaped text safe for HTML
        """
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )

    def generate_html(self, lines: List[str], auto_scroll: bool = True) -> str:
        """
        Convert list of output lines to styled HTML.

        This method is kept for backward compatibility but now delegates
        to generate_initial_html after updating internal state.

        Args:
            lines: List of console output lines
            auto_scroll: Whether to automatically scroll to bottom on load

        Returns:
            HTML string with styled console output
        """
        self.update_content(lines)
        return self.generate_initial_html(auto_scroll=auto_scroll)

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
