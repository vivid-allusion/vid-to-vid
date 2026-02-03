"""Output generation and documentation for video processing."""

import json
from loguru import logger

from ..models.generation import GenerationContext
from ..output.json_generator import generate_json_payload
from ..output.markdown_generator import generate_markdown_report
from ..output.log_generator import generate_log_content
from ..output.file_manager import FileManager


def save_generation_files(context: GenerationContext, video_filename_stem: str) -> None:
    """
    Save comprehensive documentation for video generation.

    Args:
        context: GenerationContext with all required data for output generation
        video_filename_stem: Video filename stem to use as prefix for all documentation files
    """
    try:
        payload = generate_json_payload(context)

        json_path = context.output_dir / f"{video_filename_stem}.json"
        with open(json_path, "w") as f:
            json.dump(payload, f, indent=2)
        logger.debug(f"Saved JSON payload: {json_path}")

        markdown_content = generate_markdown_report(context)

        markdown_path = context.output_dir / f"{video_filename_stem}.md"
        markdown_path.write_text(markdown_content)
        logger.debug(f"Saved markdown report: {markdown_path}")

        log_content = generate_log_content(context)

        log_path = context.output_dir / f"{video_filename_stem}.log"
        log_path.write_text(log_content)
        logger.debug(f"Saved generation log: {log_path}")

        file_manager = FileManager()
        file_manager.copy_source_file(
            context.prompt_file,
            context.output_dir,
            video_filename_stem,
        )

        if context.failed:
            logger.warning(f"📝 Saved failure documentation to {context.output_dir}")
        else:
            logger.info(f"📝 Saved all documentation files to {context.output_dir}")

    except Exception as e:
        logger.warning(f"Failed to save some documentation files: {e}")
