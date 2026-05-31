"""Main entry point for motion control video generation."""

import sys
from loguru import logger
from pathlib import Path
from typing import Dict, Any, Optional

from .utils.epic_progress import ProgressBar
from .api.client import ReplicateClient
from .config.settings import INPUT_DIR, PROFILES_DIR, OUTPUT_DIR
from .processing.processor import process_files
from .processing.profile_loader import load_active_profile
from .models.processing import ProcessingContext
from .models.video_processing import APIClientConfig
from .output.reporter import create_success_report, create_cost_report

from .utils.logging import setup_logging
from .utils.cleanup import archive_and_cleanup_logs
from .validation.environment import validate_environment, validate_input_directories
from .utils.verbose_output import show_project_header
from .utils.error_handling import run_with_error_handling


def _process_and_report(
    client: ReplicateClient, profile: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Execute processing and generate reports."""
    logger.info(f"Starting video generation with profile '{profile['name']}'")

    with ProgressBar() as progress:
        context = ProcessingContext(
            client=client,
            input_dir=INPUT_DIR,
            profiles_dir=PROFILES_DIR,
            output_dir=OUTPUT_DIR,
            progress=progress,
        )
        return process_files(context)


def _run() -> int:
    """Main entry point for image-to-video generation."""

    api_key = validate_environment()
    validate_input_directories(INPUT_DIR, PROFILES_DIR)

    profile = load_active_profile(PROFILES_DIR)
    project_name = profile.get("project_name")

    setup_logging(project_name=project_name)
    show_project_header([profile])

    config = APIClientConfig(api_token=api_key)
    client = ReplicateClient(config=config)

    results = _process_and_report(client, profile)
    if results is None:
        return 1

    output_dir = results["output_dir"]
    create_success_report(results, output_dir)
    create_cost_report(results, output_dir)

    logger.success(f"✅ Completed: {results['success']}/{results['total']} videos")
    logger.info(f"Total cost: ${results['cost']:.2f}")
    logger.info(f"Output directory: {output_dir}")

    try:
        archive_and_cleanup_logs(output_dir)
    except Exception as e:
        logger.warning(f"Failed to cleanup logs (non-fatal): {e}")

    return 0


def main() -> int:
    """Main entry point with error handling."""
    return run_with_error_handling(_run)


if __name__ == "__main__":
    sys.exit(main())
