import sys
import argparse
from open_webui import serve

def main():
    """
    Startup script for open-webui service.
    
    Imports open-webui as a package and runs the serve method
    with specified host and port parameters.
    """
    parser = argparse.ArgumentParser(description="Start Open WebUI server")
    parser.add_argument("--host", type=str, required=True, help="Host to bind to")
    parser.add_argument("--port", type=int, required=True, help="Port to bind to")
    
    args = parser.parse_args()
    
    try:
        # Call serve method with host and port parameters
        serve(host=args.host, port=args.port)
        
    except ImportError as e:
        print(f"Error: Failed to import open-webui package: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to start open-webui: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
