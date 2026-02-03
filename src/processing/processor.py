"""Video generation processor with matrix handling."""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from loguru import logger
from rich.progress import Progress

from ..api.client import ReplicateClient
from .input_discovery import discover_motion_control_jobs, parse_motion_control_job
from .profile_loader import load_active_profiles
from .cost_calculator import calculate_motion_control_cost
from .output_generator import save_generation_files
from ..utils.filename_utils import generate_video_filename
from ..models.generation import GenerationContext
from ..models.processing import ProcessingContext
from ..models.triplet import MotionControlJob
from ..models.video_processing import MotionControlRequest
from .generation_logger import log_generation_start, log_generation_complete
from ..utils.path_validator import validate_custom_paths


def _create_run_directory(
    output_dir: Path, active_profiles: List[Dict[str, Any]]
) -> Path:
    """Create timestamped output directory for this run."""
    timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
    dir_name = f"{timestamp}_MO-CONTROL"
    run_dir = output_dir / dir_name
    run_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {run_dir}")
    return run_dir


def _discover_jobs_for_profiles(
    default_input_dir: Path, profiles: List[Dict[str, Any]]
) -> Dict[str, List[MotionControlJob]]:
    """
    Discover motion control jobs for all profiles, handling custom input paths.

    Args:
        default_input_dir: Default input directory (USER-FILES/04.INPUT)
        profiles: List of profile configurations

    Returns:
        Dictionary mapping input path (string) to list of MotionControlJob objects
    """
    unique_paths: Dict[str, Path] = {str(default_input_dir): default_input_dir}

    for profile in profiles:
        custom_input = profile.get("custom_input_path")
        if custom_input:
            unique_paths[custom_input] = Path(custom_input)

    jobs_by_path: Dict[str, List[MotionControlJob]] = {}

    for path_str, path_obj in unique_paths.items():
        try:
            markdown_files = discover_motion_control_jobs(
                path_obj, path_str if path_str != str(default_input_dir) else None
            )
            jobs = [parse_motion_control_job(md_file) for md_file in markdown_files]
            jobs_by_path[path_str] = jobs
            logger.info(f"Discovered {len(jobs)} motion control jobs from {path_obj}")
        except FileNotFoundError as e:
            logger.warning(f"Input directory not found: {path_obj} - skipping")
            jobs_by_path[path_str] = []

    return jobs_by_path


def _get_output_dir_for_profile(
    default_output_dir: Path, profile: Dict[str, Any], run_timestamp: str
) -> Path:
    """
    Get the output directory for a profile, creating subdirectory if needed.

    Args:
        default_output_dir: Default output directory (USER-FILES/05.OUTPUT)
        profile: Profile configuration
        run_timestamp: Timestamp for subdirectory naming

    Returns:
        Path to output directory for this profile
    """
    custom_output = profile.get("custom_output_path")

    if custom_output:
        output_dir = Path(custom_output)
        profile_suffix = (
            str(profile["name"]).strip().replace("/", "-").replace(" ", "_")
        )
        subdir_name = f"{run_timestamp}_{profile_suffix}"
        output_dir = output_dir / subdir_name
    else:
        output_dir = default_output_dir

    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _process_all_videos(
    client: ReplicateClient,
    jobs_by_path: Dict[str, List[MotionControlJob]],
    active_profiles: List[Dict[str, Any]],
    default_output_dir: Path,
    run_timestamp: str,
    progress: Optional[Progress] = None,
) -> Tuple[int, float]:
    """Process all motion control video generations in the matrix."""
    total = sum(len(jobs) for jobs in jobs_by_path.values()) * len(active_profiles)
    success_count = 0
    total_cost = 0.0

    task_id = None
    if progress:
        task_id = progress.add_task("Generating motion control videos", total=total)

    for profile in active_profiles:
        custom_input = profile.get("custom_input_path", str(default_output_dir))
        jobs = jobs_by_path.get(custom_input, [])

        if not jobs:
            logger.info(
                f"No jobs found for profile {profile['name']} (input: {custom_input})"
            )
            continue

        profile_output_dir = _get_output_dir_for_profile(
            default_output_dir, profile, run_timestamp
        )

        for job in jobs:
            video_cost = _process_single_video(client, job, profile, profile_output_dir)

            success_count += 1
            total_cost += video_cost

            if progress and task_id is not None:
                progress.advance(task_id)

    return success_count, total_cost


def process_matrix(context: ProcessingContext) -> Dict[str, Any]:
    """
    Process motion control job files with profile matrix for video generation.

    Args:
        context: ProcessingContext with all required paths and client

    Returns:
        Dictionary with processing results

    Raises:
        Exception: On any processing failure (fail-fast)
    """
    active_profiles = load_active_profiles(context.profiles_dir)
    logger.info(f"Loaded {len(active_profiles)} video profiles")

    for profile in active_profiles:
        custom_input = profile.get("custom_input_path")
        custom_output = profile.get("custom_output_path")
        if custom_input or custom_output:
            validate_custom_paths(
                Path(custom_input) if custom_input else None,
                Path(custom_output) if custom_output else None,
            )

    jobs_by_path = _discover_jobs_for_profiles(context.input_dir, active_profiles)

    run_timestamp = datetime.now().strftime("%y%m%d_%H%M%S")

    success_count, total_cost = _process_all_videos(
        context.client,
        jobs_by_path,
        active_profiles,
        context.output_dir,
        run_timestamp,
        context.progress,
    )

    total = sum(len(jobs) for jobs in jobs_by_path.values()) * len(active_profiles)

    return {
        "total": total,
        "success": success_count,
        "failed": total - success_count,
        "cost": total_cost,
        "output_dir": context.output_dir,
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
