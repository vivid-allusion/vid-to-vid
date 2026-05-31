#!/usr/bin/env python
"""Standalone cost estimation script - calculates costs without generating videos."""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

from src.processing.input_discovery import discover_markdown_jobs, parse_markdown_job
from src.processing.profile_loader import load_active_profile
from src.processing.cost_calculator import calculate_video_cost
from src.output.file_manager import create_timestamped_directory
from src.config.settings import INPUT_DIR, PROFILES_DIR, OUTPUT_DIR
from src.models.triplet import MarkdownJob
from loguru import logger


def load_estimation_data() -> Tuple[Dict[str, Any], List[MarkdownJob]]:
    """
    Load single profile and discover markdown jobs.

    Returns:
        Tuple of (profile, jobs)

    Raises:
        Exception: If loading fails
    """
    profile = load_active_profile(PROFILES_DIR)
    logger.info(f"Loaded profile: {profile['name']}")

    markdown_files = discover_markdown_jobs(INPUT_DIR)
    jobs = [parse_markdown_job(md_file) for md_file in markdown_files]
    logger.info(f"Found {len(jobs)} markdown job files")

    return profile, jobs


def calculate_cost(
    profile: Dict[str, Any], jobs: List[MarkdownJob]
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Calculate costs for the single profile and video durations.

    Args:
        profile: Single profile dictionary
        jobs: List of MarkdownJob objects

    Returns:
        Tuple of (cost_data, duration_list)
    """
    frame_data = []

    for job in jobs:
        try:
            frame_data.append(
                {"prompt": job.markdown_file.stem, "frames": job.num_frames}
            )
            logger.info(f"{job.markdown_file.stem}: {job.num_frames} frames")
        except Exception as e:
            logger.error(f"Failed to read frames from {job.markdown_file}: {e}")
            continue

    profile_total_seconds = 0
    duration_list = []

    for item in frame_data:
        frames = item["frames"]
        was_adjusted = False
        adjustment_info = None

        if "duration_config" in profile:
            dur_config = profile["duration_config"]
            duration_type = dur_config.get("duration_type", "frames")
            min_dur = dur_config.get("min_duration", 0)
            max_dur = dur_config.get("max_duration", float("inf"))

            if duration_type == "frames":
                adjusted_duration = frames
                if adjusted_duration < min_dur:
                    adjusted_duration = min_dur
                    was_adjusted = True
                elif adjusted_duration > max_dur:
                    adjusted_duration = max_dur
                    was_adjusted = True
                fps = dur_config.get("fps", 24)
                duration_seconds = int(adjusted_duration / fps)
            else:
                adjusted_duration = frames
                if adjusted_duration < min_dur:
                    adjusted_duration = int(min_dur)
                    was_adjusted = True
                elif adjusted_duration > max_dur:
                    adjusted_duration = int(max_dur)
                    was_adjusted = True
                duration_seconds = adjusted_duration
        else:
            fps = 24
            duration_seconds = int(frames / fps)

        profile_total_seconds += duration_seconds
        duration_list.append(
            {
                "prompt": item["prompt"],
                "frames": item["frames"],
                "duration": duration_seconds,
                "adjusted": was_adjusted,
            }
        )

    total_cost = calculate_video_cost(profile, profile_total_seconds)
    cost_per_video = total_cost / len(jobs) if jobs else 0

    pricing = profile.get("pricing", {})
    cost_per_second = pricing.get("cost_per_second", 0)

    cost_data = {
        "profile": profile["name"],
        "model": profile["model_id"],
        "cost_per_second": cost_per_second,
        "total_seconds": profile_total_seconds,
        "total_cost": total_cost,
        "cost_per_video": cost_per_video,
        "num_videos": len(jobs),
    }

    logger.info(
        f"Profile '{profile['name']}': ${total_cost:.4f} for {profile_total_seconds}s total video"
    )

    return cost_data, duration_list


def generate_cost_report(
    cost_data: Dict[str, Any],
    duration_list: List[Dict[str, Any]],
    num_jobs: int,
) -> Path:
    """
    Generate markdown cost estimation report.

    Args:
        cost_data: Cost calculation for the profile
        duration_list: List of video durations
        num_jobs: Number of markdown job files

    Returns:
        Path to generated report
    """
    output_dir = create_timestamped_directory(OUTPUT_DIR, "IMG-TO-VID")
    report_path = output_dir / "cost_estimate.md"

    with open(report_path, "w") as f:
        f.write("# Cost Estimation Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## Summary\n\n")
        f.write(f"- **Total Videos:** {num_jobs}\n")
        f.write(f"- **Profile:** {cost_data['profile']}\n")
        f.write(f"- **Model:** {cost_data['model']}\n")
        f.write(f"- **Cost/Second:** ${cost_data['cost_per_second']:.4f}\n")
        f.write(f"- **Total Duration:** {cost_data['total_seconds']}s\n")
        f.write(f"- **Total Cost:** **${cost_data['total_cost']:.4f}**\n")
        f.write(f"- **Avg Cost/Video:** ${cost_data['cost_per_video']:.4f}\n\n")

        f.write("## Video Duration Distribution\n\n")
        f.write("| Video | Input Frames | Video Duration |\n")
        f.write("|-------|--------------|----------------|\n")
        for item in duration_list:
            adjusted_marker = " ⚠️" if item.get("adjusted") else ""
            f.write(
                f"| {item['prompt']} | {item['frames']} | {item['duration']}s{adjusted_marker} |\n"
            )

        total_first = sum(item["duration"] for item in duration_list)
        f.write(f"| **TOTAL** | - | **{total_first}s** |\n\n")
        f.write("*⚠️ = Duration adjusted to meet model min/max constraints*\n\n")

        f.write("## Notes\n\n")
        f.write("- All pricing is time-based (cost per second of video output)\n")
        f.write("- This is an estimate based on the active profile\n")
        f.write("- Actual costs may vary if generation fails or retries are needed\n")

    return report_path


def estimate_costs() -> None:
    """Calculate and report cost estimates without generating videos."""
    logger.info("Starting cost estimation...")

    try:
        profile, jobs = load_estimation_data()

        cost_data, duration_list = calculate_cost(profile, jobs)

        report_path = generate_cost_report(cost_data, duration_list, len(jobs))

        logger.info(f"Cost estimation report saved to: {report_path}")
        logger.success(f"✅ Cost estimation complete! Report saved to: {report_path}")

    except Exception as e:
        logger.error(f"Cost estimation failed: {e}")
        raise


if __name__ == "__main__":
    estimate_costs()
