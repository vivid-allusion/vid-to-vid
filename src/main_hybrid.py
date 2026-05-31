"""Main entry point with HYBRID progress (alive-progress WAVES + Rich logging)."""

import sys
from loguru import logger

from .api.client import ReplicateClient
from .config.settings import INPUT_DIR, PROFILES_DIR, OUTPUT_DIR
from .processing.hybrid_processor import process_files_hybrid
from .models.processing import ProcessingContext
from .models.video_processing import APIClientConfig
from .output.reporter import create_success_report, create_cost_report
from .utils.enhanced_logging import setup_dual_logging
from .utils.verbose_output import log_stage_emoji
from .utils.cleanup import archive_and_cleanup_logs
from .validation.environment import validate_environment, validate_input_directories
from .utils.error_handling import run_with_error_handling


def _run() -> int:
    """
    Main entry point with HYBRID progress (manifesto recommended approach).

    Uses BOTH libraries as recommended:
    - alive-progress: Main task with WAVES animation (maximum visual flair!)
    - Rich: Detailed sub-operation logging (professional formatting)
    """

    setup_dual_logging(enable_verbose=True)

    log_stage_emoji(
        "starting", "🌊 Initializing HYBRID mode (alive-progress WAVES + Rich)"
    )
    api_key = validate_environment()
    logger.success("Authentication successful")

    log_stage_emoji("preparing", "Validating input directories...")
    validate_input_directories(INPUT_DIR, PROFILES_DIR)
    logger.success("All input directories validated")

    config = APIClientConfig(api_token=api_key)
    client = ReplicateClient(config=config)

    context = ProcessingContext(
        client=client,
        input_dir=INPUT_DIR,
        profiles_dir=PROFILES_DIR,
        output_dir=OUTPUT_DIR,
        progress=None,
    )

    logger.info("═" * 70)
    logger.info("🌊 HYBRID MODE: alive-progress WAVES + Rich Console Logging")
    logger.info("═" * 70)

    results = process_files_hybrid(context)

    log_stage_emoji("saving", "Generating reports...")
    output_dir = results["output_dir"]
    create_success_report(results, output_dir)
    create_cost_report(results, output_dir)

    if results.get("adjustments"):
        logger.info(f"⚠️ {len(results['adjustments'])} duration adjustments made")

    log_stage_emoji("saving", "Archiving log files...")
    try:
        archive_and_cleanup_logs(output_dir)
    except Exception as e:
        logger.warning(f"Failed to cleanup logs (non-fatal): {e}")

    logger.info("═" * 70)
    logger.success(f"✅ Total cost: ${results['cost']:.2f}")
    logger.info(f"📁 Output: {output_dir}")
    logger.info("═" * 70)

    return 0


def main() -> int:
    """Main entry point with error handling."""
    return run_with_error_handling(_run)


if __name__ == "__main__":
    sys.exit(main())
