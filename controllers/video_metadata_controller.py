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

        # Connecte le bouton OK de la vue à la méthode de sauvegarde
        if hasattr(self.view, "ok_button"):
            self.view.ok_button.clicked.connect(self.handle_ok_button)

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

    # ------------------------------------------------------------------ #
    # Bouton OK - validation manuelle
    # ------------------------------------------------------------------ #
    def handle_ok_button(self) -> None:
        """
        Triggered when the OK button is clicked.
        Saves current metadata if a video is selected.
        """
        if not self._current_video:
            QMessageBox.warning(
                self.view,
                "Aucune vidéo sélectionnée",
                "Veuillez sélectionner une vidéo avant de valider.",
            )
            return

        # Récupération des valeurs actuelles depuis la vue
        payload = self.view.get_specific_metadata_inputs()
        self.on_specific_metadata_save(self._current_video, payload)
