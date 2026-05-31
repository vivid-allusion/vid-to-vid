"""Error handling wrapper for main entry points."""

from typing import Callable
from loguru import logger

from ..utils.verbose_output import log_stage_emoji
from ..exceptions import VideoGenerationError, AuthenticationError, InputValidationError


def run_with_error_handling(func: Callable[[], int]) -> int:
    """
    Run a main function with standardized error handling.

    All entry points share the same error handling pattern:
    - KeyboardInterrupt → return 130
    - AuthenticationError → return 2
    - InputValidationError → return 3
    - VideoGenerationError → return 4
    - Exception → return 1

    Args:
        func: Main function to execute

    Returns:
        Exit code
    """
    try:
        return func()
    except KeyboardInterrupt:
        log_stage_emoji("failed", "Interrupted by user")
        return 130
    except AuthenticationError as e:
        log_stage_emoji("failed", f"Authentication failed: {e}")
        return 2
    except InputValidationError as e:
        log_stage_emoji("failed", f"Input validation failed: {e}")
        return 3
    except VideoGenerationError as e:
        log_stage_emoji("failed", f"Video generation error: {e}")
        logger.exception("Full traceback:")
        return 4
    except Exception as e:
        log_stage_emoji("failed", f"Fatal error: {e}")
        logger.exception("Full traceback:")
        return 1
