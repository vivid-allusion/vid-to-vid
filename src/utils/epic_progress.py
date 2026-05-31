"""Epic progress bar implementation using alive-progress."""

from typing import TYPE_CHECKING, Optional, Any, Callable, Union
from contextlib import contextmanager
from loguru import logger

from ..config.constants import ALIVE_PROGRESS_OPTIONS

if TYPE_CHECKING:
    from alive_progress import alive_bar

    ALIVE_PROGRESS_AVAILABLE = True
else:
    try:
        from alive_progress import alive_bar

        ALIVE_PROGRESS_AVAILABLE = True
    except ImportError:
        ALIVE_PROGRESS_AVAILABLE = False
        alive_bar = None


class ProgressBar:
    """Simple progress bar wrapper using alive-progress."""

    def __init__(self, **kwargs: Any) -> None:
        self._bars: dict = {}
        self._task_counter = 0
        self._kwargs = kwargs

    def __enter__(self) -> "ProgressBar":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        for bar in self._bars.values():
            if bar is not None:
                try:
                    bar.__exit__(exc_type, exc_val, exc_tb)
                except Exception:
                    pass
        return False

    def add_task(
        self,
        description: str,
        total: Optional[int] = None,
        start: bool = True,
        **kwargs: Any,
    ) -> str:
        """Add a new task/progress bar."""
        task_id = f"task_{self._task_counter}"
        self._task_counter += 1

        if not start:
            self._bars[task_id] = None
            return task_id

        bar_options: dict = {
            "total": total,
            "title": description,
            **self._kwargs,
            **kwargs,
        }

        if ALIVE_PROGRESS_AVAILABLE and alive_bar:
            bar = alive_bar(**bar_options)
            self._bars[task_id] = bar
        else:
            self._bars[task_id] = None

        return task_id

    def update(
        self,
        task_id: str,
        advance: Union[int, float] = 0,
        set_description: Optional[str] = None,
        set_total: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        """Update task progress."""
        bar = self._bars.get(task_id)
        if bar is None:
            return

        if set_total is not None:
            try:
                bar._current = min(int(set_total), int(getattr(bar, "_current", 0)))
            except Exception:
                pass

        if advance > 0:
            try:
                bar(advance)
            except Exception:
                pass

        status = kwargs.get("status") or kwargs.get("comment")
        if status and hasattr(bar, "text"):
            bar.text = str(status)

    def stop(self) -> None:
        """Stop all bars."""
        for bar in self._bars.values():
            if bar is not None:
                try:
                    bar.stop()
                except Exception:
                    pass
        self._bars.clear()

    def advance(self, task_id: str, advance: float = 1) -> None:
        """Advance a task."""
        bar = self._bars.get(task_id)
        if bar is not None:
            try:
                bar(advance)
            except Exception:
                pass


class VideoGenerationProgress:
    """Video generation progress with alive-progress."""

    def __init__(self) -> None:
        self.progress: Optional[ProgressBar] = None
        self.main_task_id: Optional[str] = None

    @contextmanager
    def track_generation(self, total_videos: int, title: str = "Video Generation"):
        """Track video generation progress."""
        self.progress = ProgressBar(
            title=f"🎬 {title}",
            **ALIVE_PROGRESS_OPTIONS,
        )

        self.progress.__enter__()

        self.main_task_id = self.progress.add_task(
            f"Processing {total_videos} videos",
            total=total_videos,
        )

        try:
            yield self.progress, self.main_task_id
        finally:
            if self.progress:
                self.progress.__exit__(None, None, None)
            self.progress = None
            self.main_task_id = None

    def update_status(
        self,
        progress: ProgressBar,
        task_id: str,
        status: str,
        video_name: Optional[str] = None,
        phase: Optional[str] = None,
    ) -> None:
        """Update progress status."""
        status_parts = []
        if phase:
            status_parts.append(f"[yellow]{phase}")
        status_parts.append(status)
        status_text = " | ".join(status_parts)

        if video_name:
            desc = f"[cyan]{video_name}"
            progress.update(task_id, set_description=desc, status=status_text)
        else:
            progress.update(task_id, status=status_text)

    def update_with_cost(
        self,
        progress: ProgressBar,
        task_id: str,
        status: str,
        total_cost: float,
        video_name: Optional[str] = None,
    ) -> None:
        """Update progress with cost."""
        status_text = f"{status} | [green]${total_cost:.2f}"

        if video_name:
            desc = f"[cyan]{video_name}"
            progress.update(task_id, set_description=desc, status=status_text)
        else:
            progress.update(task_id, status=status_text)

    def mark_error(
        self, progress: ProgressBar, task_id: str, video_name: str, error_msg: str
    ) -> None:
        """Mark video as failed."""
        progress.update(
            task_id,
            set_description=f"[red]{video_name}",
            status=f"[red]❌ Failed: {error_msg[:50]}",
        )
        logger.error(f"✗ {video_name}: {error_msg}")

    def mark_success(
        self, progress: ProgressBar, task_id: str, video_name: str, cost: float
    ) -> None:
        """Mark video as complete."""
        progress.update(
            task_id,
            set_description=f"[green]{video_name}",
            status=f"[green]✅ Complete (${cost:.2f})",
        )
        logger.success(f"✓ {video_name} - ${cost:.2f}")


from ..config.constants import STATUS_EMOJIS


def create_api_callback(
    progress: ProgressBar, task_id: str, **kwargs: Any
) -> Callable[[str, Optional[float]], None]:
    """Create callback for API polling progress."""

    def callback(status: str, percentage: Optional[float]) -> None:
        emoji = STATUS_EMOJIS.get(status.lower(), "▶️")

        if percentage is not None:
            status_text = f"{emoji} {status.title()} ({percentage:.0f}%)"
        else:
            status_text = f"{emoji} {status.title()}"

        progress.update(task_id, status=status_text)

    return callback
