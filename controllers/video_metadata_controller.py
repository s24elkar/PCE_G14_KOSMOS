from __future__ import annotations

from PyQt6.QtWidgets import QMessageBox

from models.video_metadata_model import VideoMetadataModel


class VideoMetadataController:
    """
    Handles per-video metadata updates for the tri workflow.
    """

    def __init__(self, view, model: VideoMetadataModel):
        self.view = view
        self.model = model
        self._current_video: str | None = None

        self.view.set_specific_metadata_controller(self)

    # ------------------------------------------------------------------ #
    # Controller entry points
    # ------------------------------------------------------------------ #
    def set_current_video(self, video_name: str) -> None:
        self._current_video = video_name
        metadata = self.model.get_metadata(video_name)
        if not metadata:
            # Provide defaults to let the operator fill data.
            metadata = {
                "espece": "",
                "lieu": "",
                "commentaire": "",
            }
        self.view.show_specific_metadata(video_name, metadata)

    def clear_selection(self) -> None:
        self._current_video = None
        self.view.clear_specific_metadata()

    def on_specific_metadata_save(self, video_name: str, payload: dict) -> None:
        self.model.set_metadata(video_name, payload)
        self.view.show_specific_metadata(video_name, payload)
        QMessageBox.information(
            self.view,
            "Succès",
            "Modifié avec succès",
        )

    # ------------------------------------------------------------------ #
    # Coordination helpers
    # ------------------------------------------------------------------ #
    def rename_video(self, old_name: str, new_name: str) -> None:
        self.model.rename_video(old_name, new_name)
        if self._current_video == old_name:
            self._current_video = new_name
            self.view.show_specific_metadata(
                new_name, self.model.get_metadata(new_name)
            )

    def remove_video(self, video_name: str) -> None:
        self.model.delete_metadata(video_name)
        if self._current_video == video_name:
            self.clear_selection()
