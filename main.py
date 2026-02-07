import sys
from app.logger import setup_logging, get_logger
from app.app_controller import AppController
from app.single_instance import SingleInstance
from app.config import SINGLE_INSTANCE_NAME


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
    single_instance = None
    exit_code = 0

    try:
        # Acquire single instance lock
        single_instance = SingleInstance(SINGLE_INSTANCE_NAME)
        if not single_instance.acquire():
            logger.error("Another instance is already running.")
            return 1

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

        # Release single instance lock
        if single_instance:
            try:
                logger.info("Releasing single instance lock")
                single_instance.release()
            except Exception as e:
                logger.error(
                    f"Error releasing single instance lock: {e}", exc_info=True
                )

        logger.info("=" * 60)
        logger.info(f"Open WebUI Launcher - Exiting (code: {exit_code})")
        logger.info("=" * 60)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
