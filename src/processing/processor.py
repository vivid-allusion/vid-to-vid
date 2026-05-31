"""Video generation processor for single-profile file processing."""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from loguru import logger
from rich.progress import Progress

from ..api.client import ReplicateClient
from .input_discovery import discover_motion_control_jobs, parse_motion_control_job
from .profile_loader import load_active_profile
from .cost_calculator import calculate_motion_control_cost
from .output_generator import save_generation_files
from ..output.file_manager import FileManager, create_timestamped_directory
from ..utils.filename_utils import generate_video_filename
from ..models.generation import GenerationContext
from ..models.processing import ProcessingContext
from ..models.triplet import MotionControlJob
from ..models.video_processing import MotionControlRequest
from .generation_logger import log_generation_start, log_generation_complete
from ..utils.path_validator import validate_custom_paths


def _discover_jobs(input_dir: Path) -> List[MotionControlJob]:
    """Discover motion control jobs from the input directory."""
    markdown_files = discover_motion_control_jobs(input_dir, None)
    jobs = [parse_motion_control_job(md_file) for md_file in markdown_files]
    logger.info(f"Discovered {len(jobs)} motion control jobs from {input_dir}")
    return jobs


def _process_all_videos(
    client: ReplicateClient,
    jobs: List[MotionControlJob],
    profile: Dict[str, Any],
    run_dir: Path,
    progress: Optional[Progress] = None,
) -> Tuple[int, float]:
    """Process all motion control video generations."""
    total = len(jobs)
    success_count = 0
    total_cost = 0.0

    task_id = None
    if progress:
        task_id = progress.add_task("Generating motion control videos", total=total)

    for job in jobs:
        video_cost = _process_single_video(client, job, profile, run_dir)

        success_count += 1
        total_cost += video_cost

        if progress and task_id is not None:
            progress.advance(task_id)

    return success_count, total_cost


def process_files(context: ProcessingContext) -> Dict[str, Any]:
    """
    Process motion control job files with a single profile for video generation.

    Args:
        context: ProcessingContext with all required paths and client

    Returns:
        Dictionary with processing results

    Raises:
        Exception: On any processing failure (fail-fast)
    """
    profile = load_active_profile(context.profiles_dir)
    logger.info(f"Processing files with profile '{profile['name']}'")

    custom_input = profile.get("custom_input_path")
    custom_output = profile.get("custom_output_path")
    if custom_input or custom_output:
        validate_custom_paths(
            Path(custom_input) if custom_input else None,
            Path(custom_output) if custom_output else None,
        )

    jobs = _discover_jobs(context.input_dir)

    run_dir = create_timestamped_directory(context.output_dir, "MO-CONTROL", custom_output)

    success_count, total_cost = _process_all_videos(
        context.client,
        jobs,
        profile,
        run_dir,
        context.progress,
    )

    total = len(jobs)

    return {
        "total": total,
        "success": success_count,
        "failed": total - success_count,
        "cost": total_cost,
        "output_dir": run_dir,
    }


def _apply_prompt_modifications(prompt: str, profile: Dict[str, Any]) -> str:
    """
    Apply prefix and suffix modifications to prompt based on profile configuration.

    Args:
        prompt: Original prompt text
        profile: Profile configuration dictionary

    Returns:
        Modified prompt with prefix/suffix applied

    Raises:
        ValueError: If final prompt is empty after modifications
    """
    prompt = prompt.strip()

    prefix = profile.get("prompt_prefix")
    if prefix and prefix.strip():
        prompt = f"{prefix.strip()} {prompt}" if prompt else prefix.strip()

    suffix = profile.get("prompt_suffix")
    if suffix and suffix.strip():
        prompt = f"{prompt} {suffix.strip()}" if prompt else suffix.strip()

    prompt = " ".join(prompt.split())
    if not prompt:
        raise ValueError("Final prompt is empty after applying modifications")

    return prompt


def _prepare_generation_params(
    profile: Dict[str, Any], num_frames: int
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """
    Prepare generation parameters with duration adjustment from profile config.

    Args:
        profile: Profile configuration with duration_config
        num_frames: Input frame count

    Returns:
        Tuple of (params dict, adjustment_info dict or None)
    """
    params = profile.get("params", {}).copy()
    adjustment_info: Optional[Dict[str, Any]] = None

    if "duration_config" not in profile:
        return params, adjustment_info

    dur_config = profile["duration_config"]
    duration_type = dur_config.get("duration_type", "frames")
    duration_param = dur_config.get("duration_param_name", "num_frames")
    min_dur = dur_config.get("min_duration", 0)
    max_dur = dur_config.get("max_duration", float("inf"))

    if duration_type == "frames":
        fps = dur_config.get("fps", 24)
        adjusted = num_frames
        was_adjusted = False

        if adjusted < min_dur:
            adjusted = min_dur
            was_adjusted = True
        elif adjusted > max_dur:
            adjusted = max_dur
            was_adjusted = True

        params[duration_param] = adjusted

        if was_adjusted:
            adjustment_info = {
                "type": "frames",
                "original": num_frames,
                "adjusted": adjusted,
                "reason": f"Adjusted from {num_frames} to {adjusted} frames (min={min_dur}, max={max_dur})",
            }
    else:
        adjusted = num_frames
        was_adjusted = False

        if adjusted < min_dur:
            adjusted = int(min_dur)
            was_adjusted = True
        elif adjusted > max_dur:
            adjusted = int(max_dur)
            was_adjusted = True

        params[duration_param] = adjusted

        if was_adjusted:
            adjustment_info = {
                "type": "seconds",
                "original_seconds": num_frames,
                "adjusted_seconds": adjusted,
                "fps": dur_config.get("fps", 24),
                "reason": f"Adjusted from {num_frames}s to {adjusted}s (min={min_dur}, max={max_dur})",
            }

    return params, adjustment_info


def _process_single_video(
    client: ReplicateClient,
    job: MotionControlJob,
    profile: Dict[str, Any],
    run_dir: Path,
) -> float:
    """
    Process a single motion control video generation from markdown job.

    Args:
        client: Replicate API client
        job: MotionControlJob with parsed data
        profile: Profile configuration
        run_dir: Output directory

    Returns:
        Cost of the video generation (0.0 if failed)

    Raises:
        Exception: On generation failure (after saving output files)
    """
    prompt = job.prompt
    image_url = job.image_url
    video_url = job.video_url

    original_prompt = prompt
    prompt = _apply_prompt_modifications(prompt, profile)

    processing_name = f"{job.markdown_file.stem}_X_{profile['name']}"

    logger.info(f"Processing: {processing_name}")

    try:
        log_generation_start(processing_name, profile, prompt, image_url, video_url)

        mc_request = MotionControlRequest(
            client=client,
            profile=profile,
            image_url=image_url,
            video_url=video_url,
            prompt=prompt,
            output_dir=run_dir,
            markdown_file=job.markdown_file,
        )
        video_url_result, video_path = _generate_motion_control_video(mc_request)

        video_cost = calculate_motion_control_cost(profile)

        context = GenerationContext(
            prompt_file=job.markdown_file,
            image_url_file=job.markdown_file,
            num_frames_file=job.markdown_file,
            output_dir=run_dir,
            prompt=original_prompt,
            image_url=image_url,
            num_frames=0,
            profile=profile,
            params=profile.get("params", {}),
            video_url=video_url_result,
            video_path=video_path,
            cost=video_cost,
            adjustment_info=None,
        )

        video_filename_stem = video_path.stem
        save_generation_files(context, video_filename_stem)

        log_generation_complete(video_path, video_cost)

        return video_cost

    except Exception as e:
        logger.error(f"Failed: {job.markdown_file.name} + {profile['name']}: {e}")

        error_context = GenerationContext.from_motion_control_failure(
            job=job,
            video_dir=run_dir,
            profile=profile,
            prompt=original_prompt,
            params=profile.get("params", {}),
            error_message=str(e),
        )

        video_filename_stem = f"{job.markdown_file.stem}_X_{profile['name']}_FAILED"
        save_generation_files(error_context, video_filename_stem)

        return 0.0


def _generate_motion_control_video(request: MotionControlRequest) -> Tuple[str, Path]:
    """
    Generate motion control video and download it.

    Args:
        request: MotionControlRequest with all required parameters

    Returns:
        Tuple of (video_url, video_path)
    """
    from .video_downloader import download_video

    video_url = request.client.generate_motion_control_video(
        model_name=request.profile["model_id"],
        image_url=request.image_url,
        video_url=request.video_url,
        prompt=request.prompt,
        params=request.profile.get("params", {}),
    )

    if not video_url:
        raise Exception(f"Failed to generate video for {request.markdown_file.name}")

    video_filename = generate_video_filename(request.markdown_file.name)
    video_path = request.output_dir / video_filename
    download_video(video_url, video_path)

    return video_url, video_path
