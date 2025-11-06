from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional


SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}


@dataclass(slots=True)
class MediaItem:
    """Simple container describing a media file on disk."""

    path: Path
    thumbnail_color: str = "#00CBA9"
    metadata: dict = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.path.name


class MediaModel:
    """
    Stores the exploration state for the extraction workflow.

    The controller queries this model to populate views and keeps it updated
    when the user interacts with the interface.
    """

    def __init__(self) -> None:
        self.current_directory: Optional[Path] = None
        self._videos: List[MediaItem] = []
        self._selected_index: Optional[int] = None
        self._playback_position: int = 0  # 0-1000 range (mirrors the timeline widget)
        self._corrections: dict[str, int] = {"contrast": 0, "brightness": 0}
        self.action_log: List[str] = []

    # --------------------------------------------------------------------- #
    # Media listing and selection
    # --------------------------------------------------------------------- #
    @property
    def videos(self) -> List[MediaItem]:
        return list(self._videos)

    def load_directory(self, directory: Path | str) -> List[MediaItem]:
        """
        Scan a directory and register playable media files.

        Returns the list of :class:`MediaItem` that will be exposed to the view.
        """
        folder = Path(directory)
        if not folder.is_dir():
            raise FileNotFoundError(f"{folder} is not a directory")

        self.current_directory = folder
        self._videos = [
            MediaItem(path=file, metadata=self._build_metadata(file))
            for file in sorted(folder.iterdir())
            if file.suffix.lower() in SUPPORTED_EXTENSIONS and file.is_file()
        ]
        self._selected_index = 0 if self._videos else None
        self.action_log.clear()
        return self.videos

    def as_view_payload(self) -> List[dict]:
        """
        Convert the registry into dictionaries consumed by the view.
        """
        payload: List[dict] = []
        for item in self._videos:
            payload.append(
                {
                    "name": item.name,
                    "path": str(item.path),
                    "thumbnail_color": item.thumbnail_color,
                    "metadata": item.metadata,
                }
            )
        return payload

    def select_video(self, video_name: str) -> Optional[MediaItem]:
        """
        Mark a video as selected. Returns the item when found.
        """
        for index, item in enumerate(self._videos):
            if item.name == video_name:
                self._selected_index = index
                return item
        return None

    def get_selected_video(self) -> Optional[MediaItem]:
        if self._selected_index is None:
            return None
        try:
            return self._videos[self._selected_index]
        except IndexError:
            self._selected_index = None
            return None

    def select_next(self) -> Optional[MediaItem]:
        if not self._videos:
            return None
        if self._selected_index is None:
            self._selected_index = 0
        else:
            self._selected_index = min(self._selected_index + 1, len(self._videos) - 1)
        return self.get_selected_video()

    def select_previous(self) -> Optional[MediaItem]:
        if not self._videos:
            return None
        if self._selected_index is None:
            self._selected_index = 0
        else:
            self._selected_index = max(self._selected_index - 1, 0)
        return self.get_selected_video()

    # --------------------------------------------------------------------- #
    # Playback information
    # --------------------------------------------------------------------- #
    def set_playback_position(self, position: int) -> None:
        self._playback_position = max(0, min(position, 1000))

    def get_playback_position(self) -> int:
        return self._playback_position

    # --------------------------------------------------------------------- #
    # Corrections tracking
    # --------------------------------------------------------------------- #
    def update_corrections(self, **kwargs: int) -> None:
        for key, value in kwargs.items():
            if key in self._corrections:
                self._corrections[key] = int(value)

    def get_corrections(self) -> dict[str, int]:
        return dict(self._corrections)

    # --------------------------------------------------------------------- #
    # Action logging (used by the controller to record user actions)
    # --------------------------------------------------------------------- #
    def record_action(self, action: str) -> None:
        self.action_log.append(action)

    # --------------------------------------------------------------------- #
    # Helpers
    # --------------------------------------------------------------------- #
    def _build_metadata(self, path: Path) -> dict:
        stat = path.stat()
        return {
            "time": path.stem,
            "temp": "N/A",
            "salinity": "N/A",
            "depth": "N/A",
            "pression": f"{stat.st_size} bytes",
        }


def discover_media_files(paths: Iterable[Path]) -> List[Path]:
    """
    Utility used in tests: filter a list of paths to keep playable media.
    """
    return [
        path
        for path in paths
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
