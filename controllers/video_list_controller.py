from __future__ import annotations

from typing import Iterable, Optional

from PyQt6.QtWidgets import QInputDialog, QMessageBox

from models.video_list_model import VideoItem, VideoListModel


class VideoListController:
    """
    Controls the video list widget: rename/delete actions and detail updates.
    """

    def __init__(
        self,
        view,
        model: VideoListModel,
        metadata_controller=None,
    ):
        self.view = view
        self.model = model
        self.metadata_controller = metadata_controller

        self.view.set_video_list_controller(self)
        self.refresh_list()

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def refresh_list(self) -> None:
        self.view.show_video_list(self._as_view_payload(self.model.videos()))

    def _as_view_payload(self, videos: Iterable[VideoItem]) -> list[dict]:
        return [
            {"name": v.name, "date": v.date, "duration": v.duration} for v in videos
        ]

    def _update_details(self, video: VideoItem | None) -> None:
        if video:
            self.view.show_video_details(
                name=video.name, date=video.date, duration=video.duration
            )
        else:
            self.view.clear_video_details()

    # ------------------------------------------------------------------ #
    # Slots
    # ------------------------------------------------------------------ #
    def on_video_selected(self, video_name: str) -> None:
        video = self.model.get_video(video_name)
        self._update_details(video)
        if video and self.metadata_controller:
            self.metadata_controller.set_current_video(video.name)

    def on_rename_requested(self, video_name: str) -> None:
        video = self.model.get_video(video_name)
        if video is None:
            QMessageBox.warning(
                self.view, "Erreur", f"Vidéo '{video_name}' introuvable."
            )
            return

        new_name, ok = QInputDialog.getText(
            self.view,
            "Renommer la vidéo",
            "Nouveau nom :",
            text=video.name,
        )
        if not ok:
            return
        new_name = new_name.strip()
        try:
            self.model.rename_video(video_name, new_name)
        except ValueError as exc:
            QMessageBox.warning(self.view, "Erreur", str(exc))
            return

        if self.metadata_controller:
            self.metadata_controller.rename_video(video_name, new_name)

        self.refresh_list()
        self.view.show_video_message(f"Vidéo renommée en '{new_name}'.")
        self.view.select_video_in_list(new_name)
        self._update_details(self.model.get_video(new_name))

    def on_delete_requested(self, video_name: str) -> None:
        reply = QMessageBox.question(
            self.view,
            "Confirmer la suppression",
            f"Supprimer la vidéo '{video_name}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.model.delete_video(video_name)
        except ValueError as exc:
            QMessageBox.warning(self.view, "Erreur", str(exc))
            return

        if self.metadata_controller:
            self.metadata_controller.remove_video(video_name)

        self.refresh_list()
        self.view.show_video_message(f"Vidéo '{video_name}' supprimée.")
        self._update_details(None)
