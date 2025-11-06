from __future__ import annotations

from typing import Dict, Optional


class VideoMetadataModel:
    """
    Stores per-video metadata (métadonnées propres).
    """

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, str]] = {}

    def get_metadata(self, video_name: str) -> Dict[str, str]:
        return dict(self._store.get(video_name, {}))

    def set_metadata(self, video_name: str, metadata: Dict[str, str]) -> Dict[str, str]:
        self._store[video_name] = dict(metadata)
        return self.get_metadata(video_name)

    def update_metadata(
        self, video_name: str, updates: Dict[str, str]
    ) -> Dict[str, str]:
        existing = self._store.setdefault(video_name, {})
        for key, value in updates.items():
            existing[key] = value
        return self.get_metadata(video_name)

    def rename_video(self, old_name: str, new_name: str) -> None:
        if old_name == new_name:
            return
        data = self._store.pop(old_name, None)
        if data is not None:
            self._store[new_name] = data

    def delete_metadata(self, video_name: str) -> None:
        self._store.pop(video_name, None)
