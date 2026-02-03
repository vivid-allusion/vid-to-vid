"""Generation context model."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .triplet import MarkdownJob, MotionControlJob


@dataclass
class GenerationContext:
    """Context for video generation with all required data."""

    prompt_file: Path
    image_url_file: Path
    num_frames_file: Path
    output_dir: Path
    prompt: str
    image_url: str
    num_frames: int
    profile: Dict[str, Any]
    params: Dict[str, Any]
    video_url: str
    video_path: Path
    cost: float
    adjustment_info: Optional[Dict[str, Any]] = None
    failed: bool = False
    error_message: Optional[str] = None

    @classmethod
    def from_job(
        cls,
        job: "MarkdownJob",
        video_dir: Path,
        profile: Dict[str, Any],
        prompt: str,
        params: Dict[str, Any],
        video_url: str,
        video_path: Path,
        cost: float,
        adjustment_info: Optional[Dict[str, Any]] = None,
    ) -> "GenerationContext":
        """
        Factory method to create context from job data.

        Simplifies creation by using job.markdown_file for all file fields
        and extracting job data automatically.
        """
        return cls(
            prompt_file=job.markdown_file,
            image_url_file=job.markdown_file,
            num_frames_file=job.markdown_file,
            output_dir=video_dir,
            prompt=prompt,
            image_url=job.image_url,
            num_frames=job.num_frames,
            profile=profile,
            params=params,
            video_url=video_url,
            video_path=video_path,
            cost=cost,
            adjustment_info=adjustment_info,
            failed=False,
            error_message=None,
        )

    @classmethod
    def from_failure(
        cls,
        job: "MarkdownJob",
        video_dir: Path,
        profile: Dict[str, Any],
        prompt: str,
        params: Dict[str, Any],
        error_message: str,
    ) -> "GenerationContext":
        """
        Factory method to create context for a failed generation.

        Args:
            job: MarkdownJob with parsed data
            video_dir: Output directory
            profile: Profile configuration
            prompt: The prompt used
            params: Profile parameters
            error_message: Error message describing the failure

        Returns:
            GenerationContext marked as failed
        """
        return cls(
            prompt_file=job.markdown_file,
            image_url_file=job.markdown_file,
            num_frames_file=job.markdown_file,
            output_dir=video_dir,
            prompt=prompt,
            image_url=job.image_url,
            num_frames=job.num_frames,
            profile=profile,
            params=params,
            video_url="",
            video_path=video_dir
            / f"{job.markdown_file.stem}_X_{profile['name']}_FAILED.mp4",
            cost=0.0,
            adjustment_info=None,
            failed=True,
            error_message=error_message,
        )

    @classmethod
    def from_motion_control_failure(
        cls,
        job: "MotionControlJob",
        video_dir: Path,
        profile: Dict[str, Any],
        prompt: str,
        params: Dict[str, Any],
        error_message: str,
    ) -> "GenerationContext":
        """
        Factory method to create context for a failed motion control generation.

        Args:
            job: MotionControlJob with parsed data
            video_dir: Output directory
            profile: Profile configuration
            prompt: The prompt used
            params: Profile parameters
            error_message: Error message describing the failure

        Returns:
            GenerationContext marked as failed
        """
        return cls(
            prompt_file=job.markdown_file,
            image_url_file=job.markdown_file,
            num_frames_file=job.markdown_file,
            output_dir=video_dir,
            prompt=prompt,
            image_url=job.image_url,
            num_frames=0,
            profile=profile,
            params=params,
            video_url="",
            video_path=video_dir
            / f"{job.markdown_file.stem}_X_{profile['name']}_FAILED.mp4",
            cost=0.0,
            adjustment_info=None,
            failed=True,
            error_message=error_message,
        )
