"""Constants for video generation configuration."""

from typing import Any, Dict

# Timeout Configuration (seconds)
TIMEOUT_CONNECT = 60.0  # Connection establishment timeout
TIMEOUT_READ = 600.0    # Read timeout (10 minutes for long video generation)
TIMEOUT_WRITE = 60.0    # Write timeout for uploading data
TIMEOUT_POOL = 30.0     # Connection pool timeout

# Status Emoji Mapping (all stages used across the codebase)
STATUS_EMOJIS: Dict[str, str] = {
    "starting": "🚀",
    "preparing": "📋",
    "api_call": "📡",
    "queued": "⏳",
    "processing": "⚙️",
    "downloading": "📥",
    "saving": "💾",
    "complete": "✅",
    "succeeded": "✅",
    "failed": "❌",
    "retry": "🔄",
}

# Shared alive-progress bar options (used across all progress implementations)
ALIVE_PROGRESS_OPTIONS: Dict[str, Any] = {
    "bar": "smooth",
    "spinner": "dots_waves",
    "dual_line": True,
    "stats": True,
    "monitor": True,
    "elapsed": True,
}
