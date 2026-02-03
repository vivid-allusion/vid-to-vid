"""JSON payload generation for video documentation."""

from datetime import datetime
from typing import Dict, Any

from ..models.generation import GenerationContext


def generate_json_payload(context: GenerationContext) -> Dict[str, Any]:
    """
    Create JSON payload for documentation from generation context.

    Args:
        context: GenerationContext with all generation data

    Returns:
        Dictionary containing complete generation payload
    """
    payload = {
        "timestamp": datetime.now().isoformat(),
        "model": context.profile["model_id"],
        "profile_name": context.profile["name"],
        "duration_config": context.profile.get("duration_config", {}),
        "request": {
            "image_url": context.image_url,
            "prompt": context.prompt,
            **context.params,
        },
        "response": {},
        "source_files": {
            "prompt_file": str(context.prompt_file),
            "image_url_file": str(context.image_url_file),
            "num_frames_file": str(context.num_frames_file),
        },
    }

    if context.failed:
        payload["status"] = "failed"
        payload["response"]["error"] = context.error_message
        payload["response"]["video_url"] = None
        payload["response"]["local_path"] = None
    else:
        payload["status"] = "success"
        payload["response"]["video_url"] = context.video_url
        payload["response"]["local_path"] = str(context.video_path)

    if context.adjustment_info and context.adjustment_info.get("reason"):
        payload["duration_adjustment"] = context.adjustment_info

    return payload
