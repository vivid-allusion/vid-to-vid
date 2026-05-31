"""Main entry point with verbose output enabled by default."""

import sys
from loguru import logger

from .api.client import ReplicateClient
from .config.settings import INPUT_DIR, PROFILES_DIR, OUTPUT_DIR
from .processing.verbose_processor import process_files_verbose
from .models.processing import ProcessingContext
from .models.video_processing import APIClientConfig
from .output.reporter import create_success_report, create_cost_report

from .utils.enhanced_logging import setup_dual_logging
from .utils.verbose_output import log_stage_emoji
from .utils.cleanup import archive_and_cleanup_logs
from .validation.environment import validate_environment, validate_input_directories
from .utils.error_handling import run_with_error_handling


def _run() -> int:
    """Main entry point with verbose terminal output."""

    setup_dual_logging(enable_verbose=True)

    log_stage_emoji("starting", "Validating environment and authentication...")
    api_key = validate_environment()
    logger.success("Authentication successful")

    log_stage_emoji("preparing", "Validating input directories...")
    validate_input_directories(INPUT_DIR, PROFILES_DIR)
    logger.success("Input directory and profiles validated")

    config = APIClientConfig(api_token=api_key)
    client = ReplicateClient(config=config)

    context = ProcessingContext(
        client=client,
        input_dir=INPUT_DIR,
        profiles_dir=PROFILES_DIR,
        output_dir=OUTPUT_DIR,
        progress=None,
    )

    log_stage_emoji("processing", "Starting video generation...")
    results = process_files_verbose(context)

    log_stage_emoji("saving", "Generating reports...")
    output_dir = results["output_dir"]
    create_success_report(results, output_dir)
    create_cost_report(results, output_dir)

    log_stage_emoji("saving", "Archiving log files...")
    try:
        archive_and_cleanup_logs(output_dir)
    except Exception as e:
        logger.warning(f"Failed to cleanup logs (non-fatal): {e}")

    logger.success("═" * 60)
    log_stage_emoji("complete", "All processing complete!")
    logger.success(f"✅ Success: {results['success']}/{results['total']} videos")
    logger.info(f"💰 Total cost: ${results['cost']:.2f}")
    logger.info(f"📁 Output: {output_dir}")
    logger.success("═" * 60)

    return 0


def main() -> int:
    """Main entry point with error handling."""
    return run_with_error_handling(_run)


if __name__ == "__main__":
    sys.exit(main())
