from __future__ import annotations

from pathlib import Path
from typing import Optional

from models.media_model import MediaItem, MediaModel


class ExtractionController:
    """
    Bridge layer between the extraction view and the media model.

    It listens to UI signals, updates the model accordingly and pushes
    refreshed data back to the widgets.
    """

    def __init__(self, view, model: MediaModel):
        self.view = view
        self.model = model

        # Make sure the view knows about its controller and signals are bound.
        self.view.controller = self
        self.view.connect_signals()

        # Populate the UI with whatever the model already knows.
        self.load_initial_data()

    # ------------------------------------------------------------------ #
    # Data loading helpers
    # ------------------------------------------------------------------ #
    def load_initial_data(self) -> None:
        videos = self.model.as_view_payload()
        self.view.update_video_list(videos)
        selected = self.model.get_selected_video()
        if selected:
            self._show_video(selected)

    def load_directory(self, directory: str | Path) -> None:
        videos = self.model.load_directory(directory)
        self.view.update_video_list(self.model.as_view_payload())
        if videos:
            self._show_video(videos[0])

    # ------------------------------------------------------------------ #
    # Signal handlers wired by the view
    # ------------------------------------------------------------------ #
    def on_tab_changed(self, tab_name: str) -> None:
        self.model.record_action(f"tab:{tab_name}")

    def on_video_selected(self, video_name: str) -> None:
        item = self.model.select_video(video_name)
        if item:
            self._show_video(item)

    def on_screenshot(self) -> None:
        self._register_processing_action("screenshot")

    def on_recording(self) -> None:
        self._register_processing_action("recording")

    def on_create_short(self) -> None:
        self._register_processing_action("short")

    def on_crop(self) -> None:
        self._register_processing_action("crop")

    def on_color_correction(self) -> None:
        self.model.record_action("color_correction")
        self._push_corrections_to_view()

    def on_contrast_changed(self, value: int) -> None:
        self.model.update_corrections(contrast=value)
        self._push_corrections_to_view()

    def on_brightness_changed(self, value: int) -> None:
        self.model.update_corrections(brightness=value)
        self._push_corrections_to_view()

    def on_apply_corrections(self) -> None:
        """Applique explicitement les corrections sur l'aperçu."""
        self._push_corrections_to_view()

    def on_undo_correction(self) -> None:
        """Restaure la correction précédente et met la vue à jour."""
        restored = self.model.undo_last_correction()
        if hasattr(self.view, "set_correction_values"):
            self.view.set_correction_values(restored)
        self._push_corrections_to_view()

    def on_play_pause(self) -> None:
        self.model.record_action("play_pause")

    def on_position_changed(self, position: int) -> None:
        self.model.set_playback_position(position)

    def on_previous_video(self) -> None:
        item = self.model.select_previous()
        if item:
            self._show_video(item)

    def on_next_video(self) -> None:
        item = self.model.select_next()
        if item:
            self._show_video(item)

    def on_rewind(self) -> None:
        new_position = max(self.model.get_playback_position() - 100, 0)
        self.model.set_playback_position(new_position)
        self._sync_player_position()

    def on_forward(self) -> None:
        new_position = min(self.model.get_playback_position() + 100, 1000)
        self.model.set_playback_position(new_position)
        self._sync_player_position()

    def on_view_mode_changed(self, mode: str) -> None:
        """Enregistre les changements d'affichage de l'explorateur."""
        self.model.record_action(f"view_mode:{mode}")

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _show_video(self, item: MediaItem) -> None:
        payload = {
            "name": item.name,
            "path": str(item.path),
            "metadata": item.metadata,
        }
        self.view.update_video_player(payload)
        self.view.update_histogram()

    def _sync_player_position(self) -> None:
        if hasattr(self.view, "video_player") and hasattr(
            self.view.video_player, "set_position"
        ):
            self.view.video_player.set_position(self.model.get_playback_position())

    def _push_corrections_to_view(self) -> None:
        """Envoie les corrections courantes vers l'aperçu/histogramme."""
        corrections = self.model.get_corrections()
        if hasattr(self.view, "apply_corrections_to_preview"):
            self.view.apply_corrections_to_preview(corrections)

    def _register_processing_action(self, action: str) -> None:
        self.model.record_action(action)
        current = self.model.get_selected_video()
        message = f"{action} triggered"
        if current:
            message += f" for {current.name}"
        self.view.show_message(message, "info")
