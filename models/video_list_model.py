from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass(slots=True)
class VideoItem:
    name: str
    date: str
    duration: str


class VideoListModel:
    """
    Stores the list of videos displayed in the tri workflow and exposes
    operations to rename or delete entries.
    """

    def __init__(self, videos: Optional[Iterable[VideoItem]] = None) -> None:
        self._videos: List[VideoItem] = list(videos or [])

    # ------------------------------------------------------------------ #
    # Query helpers
    # ------------------------------------------------------------------ #
    def videos(self) -> List[VideoItem]:
        return list(self._videos)

    def get_video(self, name: str) -> Optional[VideoItem]:
        for item in self._videos:
            if item.name == name:
                return item
        return None

    # ------------------------------------------------------------------ #
    # Mutating operations
    # ------------------------------------------------------------------ #
    def rename_video(self, old_name: str, new_name: str) -> VideoItem:
        if not new_name.strip():
            raise ValueError("Le nouveau nom ne peut pas être vide.")
        if self.get_video(new_name):
            raise ValueError(f"Une vidéo nommée '{new_name}' existe déjà.")
        video = self.get_video(old_name)
        if video is None:
            raise ValueError(f"Vidéo '{old_name}' introuvable.")
        video.name = new_name
        return video

    def delete_video(self, name: str) -> None:
        video = self.get_video(name)
        if video is None:
            raise ValueError(f"Vidéo '{name}' introuvable.")
        self._videos.remove(video)
