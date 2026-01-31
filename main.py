import sys
from logger import setup_logging, get_logger
from app_controller import AppController


def main() -> int:
    """
    Application entry point.

    Sets up logging, creates and initializes the application controller,
    and handles top-level exceptions and cleanup.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Set up logging
    setup_logging(level=20)  # INFO level
    logger = get_logger(__name__)

    logger.info("=" * 60)
    logger.info("Open WebUI Launcher - Starting")
    logger.info("=" * 60)

    controller = None
    exit_code = 0

    try:
        # Create application controller
        controller = AppController()

        # Initialize all components
        controller.initialize()

        # Start application (blocking call)
        controller.start_application()

        logger.info("Application exited normally")

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt (Ctrl+C)")
        logger.info("Initiating graceful shutdown...")
        exit_code = 0

    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        exit_code = 1

    finally:
        # Ensure proper shutdown - always called when window closes
        if controller:
            try:
                controller.shutdown()
            except Exception as e:
                logger.error(f"Error during shutdown: {e}", exc_info=True)
                exit_code = 1

        logger.info("=" * 60)
        logger.info(f"Open WebUI Launcher - Exiting (code: {exit_code})")
        logger.info("=" * 60)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
