"""File management utilities for output generation."""
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
from loguru import logger


def create_timestamped_directory(
    output_dir: Path, prefix: str, custom_output_path: Optional[str] = None
) -> Path:
    """
    Create a timestamped output directory.

    Args:
        output_dir: Base output directory
        prefix: Directory name prefix (e.g., 'MO-CONTROL', 'IMG-TO-VID')
        custom_output_path: Optional custom output path override

    Returns:
        Path to the created directory
    """
    base_dir = Path(custom_output_path) if custom_output_path else output_dir
    timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
    dir_name = f"{timestamp}_{prefix}"
    run_dir = base_dir / dir_name
    run_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {run_dir}")
    return run_dir


class FileManager:
    """Manager for output file operations."""

    @staticmethod
    def copy_source_file(source_file: Path, output_dir: Path,
                        video_filename_stem: str) -> None:
        """
        Copy source markdown file for reference with video filename prefix.

        Args:
            source_file: Path to source markdown file
            output_dir: Destination directory
            video_filename_stem: Video filename stem to use as prefix
        """
        try:
            dest_filename = f"{video_filename_stem}_source.md"
            shutil.copy2(source_file, output_dir / dest_filename)
            logger.debug(f"Copied source file to {output_dir / dest_filename}")
        except Exception as e:
            logger.warning(f"Failed to copy source file: {e}")
