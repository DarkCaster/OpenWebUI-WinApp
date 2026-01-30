class StatusPage:
    """
    Generate HTML content for various application states.

    Provides static methods to create simple, styled HTML pages
    for different states of the Open WebUI launcher application.
    """

    @staticmethod
    def starting_page() -> str:
        """
        Generate HTML for the starting state with a loading spinner.

        Returns:
            HTML string with loading animation and starting message
        """
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Starting Open WebUI</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    color: #ffffff;
                }
                
                .container {
                    text-align: center;
                    padding: 40px;
                }
                
                .spinner {
                    width: 60px;
                    height: 60px;
                    border: 4px solid rgba(255, 255, 255, 0.3);
                    border-top-color: #ffffff;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 30px;
                }
                
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
                
                h1 {
                    font-size: 32px;
                    font-weight: 600;
                    margin-bottom: 16px;
                }
                
                p {
                    font-size: 18px;
                    opacity: 0.9;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="spinner"></div>
                <h1>Starting Open WebUI...</h1>
                <p>Please wait while the service is initializing</p>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def stopping_page() -> str:
        """
        Generate HTML for the stopping state.

        Returns:
            HTML string with stopping message
        """
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Stopping Open WebUI</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    color: #ffffff;
                }
                
                .container {
                    text-align: center;
                    padding: 40px;
                }
                
                h1 {
                    font-size: 32px;
                    font-weight: 600;
                    margin-bottom: 16px;
                }
                
                p {
                    font-size: 18px;
                    opacity: 0.9;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Stopping Open WebUI...</h1>
                <p>Shutting down the service</p>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def stopped_page() -> str:
        """
        Generate HTML for the stopped state with instructions.

        Returns:
            HTML string with stopped message and start instructions
        """
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Open WebUI Stopped</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    color: #333333;
                }
                
                .container {
                    text-align: center;
                    padding: 40px;
                    background: rgba(255, 255, 255, 0.9);
                    border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                    max-width: 500px;
                }
                
                h1 {
                    font-size: 32px;
                    font-weight: 600;
                    margin-bottom: 20px;
                    color: #2d3748;
                }
                
                p {
                    font-size: 18px;
                    line-height: 1.6;
                    color: #4a5568;
                    margin-bottom: 12px;
                }
                
                .instructions {
                    margin-top: 24px;
                    padding: 16px;
                    background: #edf2f7;
                    border-radius: 8px;
                    border-left: 4px solid #4299e1;
                }
                
                .instructions p {
                    font-size: 16px;
                    color: #2d3748;
                }
                
                .menu-hint {
                    font-weight: 600;
                    color: #2b6cb0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Open WebUI is Stopped</h1>
                <p>The Open WebUI service is not currently running.</p>
                <div class="instructions">
                    <p>To start the service, go to <span class="menu-hint">Control → Start</span> in the menu bar.</p>
                </div>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def error_page(message: str) -> str:
        """
        Generate HTML for the error state with error details.

        Args:
            message: Error message to display

        Returns:
            HTML string with error message and details
        """
        # Escape HTML special characters in the message
        escaped_message = (
            message.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Open WebUI Error</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    background: linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    color: #ffffff;
                    padding: 20px;
                }}
                
                .container {{
                    text-align: center;
                    padding: 40px;
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
                    max-width: 600px;
                    width: 100%;
                }}
                
                .error-icon {{
                    font-size: 64px;
                    margin-bottom: 20px;
                }}
                
                h1 {{
                    font-size: 32px;
                    font-weight: 600;
                    margin-bottom: 20px;
                    color: #c53030;
                }}
                
                .error-message {{
                    font-size: 16px;
                    line-height: 1.6;
                    color: #2d3748;
                    margin-bottom: 24px;
                    padding: 16px;
                    background: #fff5f5;
                    border-radius: 8px;
                    border: 1px solid #fc8181;
                    text-align: left;
                    word-wrap: break-word;
                    font-family: 'Courier New', monospace;
                }}
                
                .instructions {{
                    margin-top: 24px;
                    padding: 16px;
                    background: #edf2f7;
                    border-radius: 8px;
                }}
                
                .instructions p {{
                    font-size: 16px;
                    color: #2d3748;
                    margin-bottom: 8px;
                }}
                
                .instructions p:last-child {{
                    margin-bottom: 0;
                }}
                
                .menu-hint {{
                    font-weight: 600;
                    color: #2b6cb0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error-icon">⚠️</div>
                <h1>An Error Occurred</h1>
                <div class="error-message">{escaped_message}</div>
                <div class="instructions">
                    <p>You can try to restart the service from <span class="menu-hint">Control → Restart</span></p>
                    <p>Check the console output for more details.</p>
                </div>
            </div>
        </body>
        </html>
        """
