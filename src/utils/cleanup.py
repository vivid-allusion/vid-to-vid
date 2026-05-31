"""Cleanup utilities for archiving and removing log files after video generation."""

import subprocess
from pathlib import Path
from datetime import datetime
from zipfile import ZipFile, ZIP_DEFLATED
from typing import List
from loguru import logger


def archive_and_cleanup_logs(output_dir: Path) -> None:
    """
    Archive all non-MP4 files to a zip and move originals to trash.

    This function:
    1. Finds all files in output_dir that are not .mp4
    2. Creates a timestamped zip file containing these files
    3. Moves the original files to trash using the 'trash' command
    4. Keeps the zip file and all .mp4 files

    Args:
        output_dir: Directory containing generated videos and log files

    Raises:
        FileNotFoundError: If trash command is not available
        subprocess.CalledProcessError: If trash command fails
    """
    if not output_dir.exists():
        logger.warning(f"Output directory does not exist: {output_dir}")
        return

    # Find all non-MP4 files
    all_files = list(output_dir.rglob("*"))
    non_mp4_files = [f for f in all_files if f.is_file() and f.suffix.lower() != ".mp4"]

    if not non_mp4_files:
        logger.info("No log files to archive")
        return

    # Create timestamp for zip filename
    timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
    zip_filename = f"{timestamp}_logs.zip"
    zip_path = output_dir / zip_filename

    # Create zip file
    logger.info(f"Archiving {len(non_mp4_files)} log files to {zip_filename}")

    try:
        with ZipFile(zip_path, 'w', ZIP_DEFLATED) as zipf:
            for file_path in non_mp4_files:
                # Store with relative path from output_dir to preserve structure
                arcname = file_path.relative_to(output_dir)
                zipf.write(file_path, arcname=arcname)
                logger.debug(f"Added to zip: {arcname}")

        logger.success(f"✅ Created archive: {zip_filename}")

        # Move original files to trash
        _trash_files(non_mp4_files)

        logger.success(f"🗑️  Moved {len(non_mp4_files)} log files to trash")
        logger.info(f"📦 Archive location: {zip_path}")

    except Exception as e:
        logger.error(f"Failed to archive and cleanup logs: {e}")
        # If zipping succeeded but trash failed, we still have the zip
        if zip_path.exists():
            logger.info(f"Archive was created successfully: {zip_path}")
        raise


def _trash_files(files: List[Path]) -> None:
    """
    Move files to trash using cross-platform approach.

    Tries: 1) 'trash' command (macOS/Linux), 2) 'gio trash' (Linux GNOME),
    3) fallback to .trash/ directory.

    Args:
        files: List of file paths to move to trash
    """
    if not files:
        return

    # Try 'trash' command first (macOS via brew, or trash-cli on Linux)
    try:
        subprocess.run(["which", "trash"], check=True, capture_output=True)
        _trash_with_command(files, "trash")
        return
    except subprocess.CalledProcessError:
        pass

    # Try 'gio trash' (GNOME desktop on Linux)
    try:
        subprocess.run(["which", "gio"], check=True, capture_output=True)
        _trash_with_command(files, "gio", args=["trash"])
        return
    except subprocess.CalledProcessError:
        pass

    # Fallback: move to .trash/ directory
    _trash_to_directory(files)


def _trash_with_command(files: List[Path], command: str, args: Optional[List[str]] = None) -> None:
    """Move files to trash using a system command."""
    cmd_args = [command]
    if args:
        cmd_args.extend(args)

    batch_size = 50
    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]
        file_paths = [str(f) for f in batch]

        try:
            subprocess.run(
                cmd_args + file_paths,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to trash files: {e.stderr}")
            raise


def _trash_to_directory(files: List[Path]) -> None:
    """Move files to .trash/ directory as fallback."""
    if not files:
        return

    # Use the parent of the first file as the base for .trash/
    base_dir = files[0].parent
    trash_dir = base_dir / ".trash"
    trash_dir.mkdir(exist_ok=True)

    for file_path in files:
        try:
            dest = trash_dir / file_path.name
            file_path.rename(dest)
            logger.debug(f"Moved to trash: {dest}")
        except Exception as e:
            logger.warning(f"Failed to trash {file_path}: {e}")
