"""Enhanced processor with verbose terminal output."""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from loguru import logger

from ..api.async_client_enhanced import AsyncReplicateClientEnhanced
from ..utils.verbose_output import VerboseContext, log_stage_emoji
from ..utils.epic_progress import VideoGenerationProgress, create_api_callback
from ..utils.filename_utils import generate_video_filename
from ..models.generation import GenerationContext
from ..models.processing import ProcessingContext
from ..models.triplet import MotionControlJob
from ..models.video_processing import VideoProcessingContext, APIClientConfig
from .cost_calculator import calculate_motion_control_cost
from .input_discovery import discover_motion_control_jobs, parse_motion_control_job
from .output_generator import save_generation_files
from .profile_loader import load_active_profiles
from .video_downloader import download_video
from .processor import _apply_prompt_modifications


def process_matrix_verbose(context: ProcessingContext) -> Dict[str, Any]:
    """
    Process video matrix with verbose terminal output.

    Args:
        context: ProcessingContext with all required paths and client

    Returns:
        Dictionary with processing results
    """
    try:
        with VerboseContext() as verbose:
            async_client, jobs, active_profiles, run_dir = _setup_processing(context)
            results = _execute_video_batch(async_client, jobs, active_profiles, run_dir)
            return _generate_summary(results, run_dir)
    except Exception:
        return {"total": 0, "success": 0, "cost": 0.0, "output_dir": context.output_dir}


def _setup_processing(
    context: ProcessingContext,
) -> Tuple[AsyncReplicateClientEnhanced, List[MotionControlJob], List, Path]:
    """Setup processing environment and discover inputs."""
    config = APIClientConfig(api_token=context.client.api_token, poll_interval=3)
    async_client = AsyncReplicateClientEnhanced(config=config)

    log_stage_emoji("preparing", "Loading video profiles...")
    active_profiles = load_active_profiles(context.profiles_dir)
    logger.success(f"Loaded {len(active_profiles)} profiles")

    log_stage_emoji("preparing", "Discovering motion control jobs...")

    custom_input_path = None
    if active_profiles:
        custom_input_path = active_profiles[0].get("custom_input_path")

    markdown_files = discover_motion_control_jobs(context.input_dir, custom_input_path)
    jobs = [parse_motion_control_job(md_file) for md_file in markdown_files]
    logger.success(f"Found {len(jobs)} motion control jobs")

    timestamp = datetime.now().strftime("%y%m%d_%H%M%S")

    custom_output_path = None
    if active_profiles:
        custom_output_path = active_profiles[0].get("custom_output_path")

    base_output_dir = (
        Path(custom_output_path) if custom_output_path else context.output_dir
    )

    dir_name = f"{timestamp}_MO-CONTROL"
    run_dir = base_output_dir / dir_name
    run_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Output: {run_dir}")

    return async_client, jobs, active_profiles, run_dir


def _execute_video_batch(
    async_client: AsyncReplicateClientEnhanced,
    jobs: List[MotionControlJob],
    active_profiles: List,
    run_dir: Path,
) -> Dict[str, Any]:
    """Execute batch video processing with epic progress tracking."""
    total = len(jobs) * len(active_profiles)

    epic_progress = VideoGenerationProgress()

    success_count = 0
    total_cost = 0.0

    with epic_progress.track_generation(
        total, title="Motion Control Video Generation"
    ) as (
        progress,
        main_task,
    ):
        for job in jobs:
            for profile in active_profiles:
                video_name = f"{job.markdown_file.stem}_X_{profile['name']}"

                try:
                    epic_progress.update_status(
                        progress,
                        main_task,
                        status="Starting...",
                        video_name=video_name,
                        phase="Initializing",
                    )

                    video_context = VideoProcessingContext(
                        client=async_client,
                        prompt_file=job.markdown_file,
                        image_url_file=job.markdown_file,
                        num_frames_file=job.markdown_file,
                        profile=profile,
                        run_dir=run_dir,
                        progress=progress,
                        task_id=main_task,
                    )

                    video_cost = _process_video_verbose(
                        video_context, job, epic_progress
                    )

                    success_count += 1
                    total_cost += video_cost

                    epic_progress.mark_success(
                        progress, main_task, video_name, video_cost
                    )

                    progress.advance(main_task)

                    epic_progress.update_with_cost(
                        progress,
                        main_task,
                        status="Complete",
                        total_cost=total_cost,
                        video_name=video_name,
                    )

                except Exception as e:
                    epic_progress.mark_error(progress, main_task, video_name, str(e))
                    logger.exception(e)
                    total_cost += 0.0

    return {
        "success_count": success_count,
        "total": total,
        "total_cost": total_cost,
    }


def _generate_summary(results: Dict[str, Any], run_dir: Path) -> Dict[str, Any]:
    """Generate final processing summary."""
    total = results["total"]
    success_count = results["success_count"]
    total_cost = results["total_cost"]

    logger.success(f"🎉 Completed {success_count}/{total} videos")
    logger.info(f"💰 Total cost: ${total_cost:.2f}")

    return {
        "total": total,
        "success": success_count,
        "cost": total_cost,
        "output_dir": run_dir,
    }


def _process_video_verbose(
    context: VideoProcessingContext,
    job: MotionControlJob,
    epic_progress: VideoGenerationProgress,
) -> float:
    """Process single video with verbose output and polling."""

    log_stage_emoji("preparing", f"Loading inputs for {job.markdown_file.stem}")
    prompt = job.prompt
    image_url = job.image_url
    video_url = job.video_url

    prompt = _apply_prompt_modifications(prompt, context.profile)

    video_name = f"{job.markdown_file.stem}_X_{context.profile['name']}"

    epic_progress.update_status(
        context.progress,
        context.task_id,
        status="Preparing API call",
        video_name=video_name,
        phase="Preparing",
    )

    logger.info("═" * 60)
    log_stage_emoji("starting", f"Generating: {video_name}")
    logger.info(f"📝 Prompt: {prompt[:80]}...")
    logger.info(f"🖼️  Image: {image_url[:80]}...")
    logger.info(f"🎬 Video Reference: {video_url[:80]}...")
    logger.info(f"⚙️  Model: {context.profile['model_id']}")
    logger.info("═" * 60)

    progress_callback = create_api_callback(context.progress, context.task_id)

    try:
        video_url_result = context.client.generate_motion_control_video_with_polling(
            model_name=context.profile["model_id"],
            image_url=image_url,
            video_url=video_url,
            prompt=prompt,
            params=context.profile.get("params", {}),
            progress_callback=progress_callback,
        )

        if not video_url_result:
            error_msg = f"No video URL returned from API for {video_name}"
            logger.error(error_msg)
            raise Exception(error_msg)

        epic_progress.update_status(
            context.progress,
            context.task_id,
            status="Downloading video",
            video_name=video_name,
            phase="Downloading",
        )

        video_filename = generate_video_filename(job.markdown_file.name)
        video_path = context.run_dir / video_filename
        download_video(video_url_result, video_path)

        video_cost = calculate_motion_control_cost(context.profile)

        epic_progress.update_status(
            context.progress,
            context.task_id,
            status="Saving documentation",
            video_name=video_name,
            phase="Finalizing",
        )

        gen_context = GenerationContext(
            prompt_file=job.markdown_file,
            image_url_file=job.markdown_file,
            num_frames_file=job.markdown_file,
            output_dir=context.run_dir,
            prompt=prompt,
            image_url=image_url,
            num_frames=0,
            profile=context.profile,
            params=context.profile.get("params", {}),
            video_url=video_url_result,
            video_path=video_path,
            cost=video_cost,
            adjustment_info=None,
        )

        video_filename_stem = video_path.stem
        save_generation_files(gen_context, video_filename_stem)

        log_stage_emoji("complete", f"Completed: {video_path.name} (${video_cost:.2f})")

        return video_cost

    except Exception as e:
        logger.error(f"Failed to generate {video_name}: {e}")

        error_context = GenerationContext.from_motion_control_failure(
            job=job,
            video_dir=context.run_dir,
            profile=context.profile,
            prompt=prompt,
            params=context.profile.get("params", {}),
            error_message=str(e),
        )

        video_filename_stem = (
            f"{job.markdown_file.stem}_X_{context.profile['name']}_FAILED"
        )
        save_generation_files(error_context, video_filename_stem)

        log_stage_emoji("failed", f"Failed: {video_name}")
        raise
