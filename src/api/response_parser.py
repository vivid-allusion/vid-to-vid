"""Response parsing utilities for Replicate API."""

from typing import Any, Optional
from loguru import logger


def extract_video_url(result: Any) -> Optional[str]:
    """
    Extract video URL from API response.

    Handles multiple response formats: string, list, FileOutput, fallback.

    Args:
        result: API response (various types possible)

    Returns:
        Video URL if found, None otherwise
    """
    if not result:
        logger.error("No result from Replicate API")
        return None

    logger.debug(f"Result type: {type(result)}, value: {result}")

    if isinstance(result, str):
        logger.info(f"Successfully got video URL: {result}")
        return result

    if hasattr(result, "url"):
        logger.info(f"Successfully got video URL from FileOutput: {result.url}")
        return result.url

    if isinstance(result, list):
        if not result:
            return None
        first_item = result[0]
        if hasattr(first_item, "url"):
            logger.info(
                f"Successfully got video URL from list FileOutput: {first_item.url}"
            )
            return first_item.url
        logger.info(f"Successfully got video URL from list: {first_item}")
        return first_item

    result_str = str(result)
    if result_str.startswith("http"):
        logger.info(f"Successfully converted result to URL: {result_str}")
        return result_str

    logger.error(
        f"Unexpected response format - type: {type(result)}, value: {result}"
    )
    return None
