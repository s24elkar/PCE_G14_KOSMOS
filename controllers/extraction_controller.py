from __future__ import annotations

import os
from pathlib import Path
import time
from typing import Optional

import cv2
import numpy as np
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QInputDialog,
    QSpinBox,
    QVBoxLayout,
)

from models.campaign_model import CampaignModel
from models.media_model import MediaItem, MediaModel


class ExtractionController:
    """
    Bridge layer between the extraction view and the media model.

    It listens to UI signals, updates the model accordingly and pushes
    refreshed data back to the widgets.
    """

    def __init__(self, view, model: MediaModel, campaign_model: CampaignModel | None = None):
        self.view = view
        self.model = model
        self.campaign_model = campaign_model
        self._current_duration: float = 0.0
        self._last_histogram_ts: float = 0.0
        self._last_export_range: tuple[int, int] | None = None

        # Make sure the view knows about its controller and signals are bound.
        self.view.controller = self
        self.view.connect_signals()

        # Populate the UI with whatever the model already knows.
        self.load_initial_data()
        self._maybe_autoload_campaign()

    # ------------------------------------------------------------------ #
    # Data loading helpers
    # ------------------------------------------------------------------ #
    def load_initial_data(self) -> None:
        videos = self.model.as_view_payload()
        self._colorize_thumbnails(videos)
        self.view.update_video_list(videos)
        selected = self.model.get_selected_video()
        if selected:
            self._show_video(selected)

    def load_directory(self, directory: str | Path) -> None:
        try:
            videos = self.model.load_directory(directory)
        except Exception as exc:
            self.view.show_message(str(exc), "error")
            return
        payload = self.model.as_view_payload()
        self._colorize_thumbnails(payload)
        self.view.update_video_list(payload)
        if videos:
            self._show_video(videos[0])
        else:
            self.view.show_message("Aucune vidéo trouvée dans ce dossier.", "warning")

    # ------------------------------------------------------------------ #
    # Signal handlers wired by the view
    # ------------------------------------------------------------------ #
    def on_tab_changed(self, tab_name: str) -> None:
        self.model.record_action(f"tab:{tab_name}")

    def on_video_selected(self, video_identifier: str) -> None:
        """
        `video_identifier` peut être un nom (hérité) ou un chemin complet.
        """
        # Si on reçoit un chemin complet, on prend juste le nom pour la sélection
        path = Path(video_identifier)
        video_name = path.name if path.suffix else video_identifier
        item = self.model.select_video(video_name)
        if item:
            self._show_video(item)
        else:
            self.view.show_message(f"Vidéo introuvable: {video_identifier}", "error")

    def on_screenshot(self) -> None:
        name = self._prompt_capture_name()
        if name is None:
            return
        path = self._current_video_path()
        if not path:
            return
        success = self._export_screenshot(path, name)
        self._register_processing_action("screenshot", details={"name": name, "ok": success})

    def on_recording(self) -> None:
        bounds = self._prompt_recording_range()
        if bounds is None:
            return
        start, end = bounds
        path = self._current_video_path()
        if not path:
            return
        self._set_export_range_visual(start, end)
        success = self._export_subclip(path, start, end, suffix="recording")
        self._register_processing_action("recording", details={"start": start, "end": end, "ok": success})

    def on_create_short(self) -> None:
        name = self._prompt_short_name()
        if name is None:
            return
        path = self._current_video_path()
        if not path:
            return
        duration = self._probe_duration(path)
        current_sec = self._current_playback_seconds(path, duration)
        start = max(current_sec - 15, 0.0)
        end = min(current_sec + 15, duration if duration else current_sec + 15)
        if duration and end - start < 30:
            end = min(duration, start + 30)
            if end - start < 30 and duration:
                start = max(0, end - 30)
        success = self._export_subclip(path, start, end, suffix=name or "short")
        self._register_processing_action("short", details={"name": name, "start": start, "end": end, "ok": success})

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
    
    def on_saturation_changed(self, value: int) -> None:
        self.model.update_corrections(saturation=value)
        self._push_corrections_to_view()

    def on_hue_changed(self, value: int) -> None:
        self.model.update_corrections(hue=value)
        self._push_corrections_to_view()

    def on_temperature_changed(self, value: int) -> None:
        self.model.update_corrections(temperature=value)
        self._push_corrections_to_view()

    def on_sharpness_changed(self, value: int) -> None:
        self.model.update_corrections(sharpness=value)
        self._push_corrections_to_view()

    def on_gamma_changed(self, value: int) -> None:
        self.model.update_corrections(gamma=value)
        self._push_corrections_to_view()

    def on_denoise_changed(self, value: int) -> None:
        self.model.update_corrections(denoise=value)
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

    def on_preset_selected(self, corrections: dict) -> None:
        """
        Applique un preset issu du composant avancé.
        """
        if corrections:
            self.model.update_corrections(**corrections)
        else:
            self.model.reset_corrections()
        if hasattr(self.view, "set_correction_values"):
            self.view.set_correction_values(self.model.get_corrections())
        self._push_corrections_to_view()
        self.model.record_action("preset_correction")

    def on_play_pause(self) -> None:
        self.model.record_action("play_pause")

    def on_position_changed(self, position: int) -> None:
        self.model.set_playback_position(position)
        path = self._current_video_path()
        if not path:
            return
        # Met à jour timecode + histogramme/aperçu de manière limitée en fréquence
        self._update_timecode(path)
        now = time.monotonic()
        if now - self._last_histogram_ts >= 0.25:
            frame = self._frame_at_position(path, position)
            if frame is not None:
                if hasattr(self.view, "video_player") and hasattr(self.view.video_player, "set_frame"):
                    self.view.video_player.set_frame(frame)
                histogram = self._compute_histogram(frame)
                self.view.update_histogram(histogram)
            self._last_histogram_ts = now

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
        self.on_position_changed(new_position)

    def on_forward(self) -> None:
        new_position = min(self.model.get_playback_position() + 100, 1000)
        self.model.set_playback_position(new_position)
        self._sync_player_position()
        self.on_position_changed(new_position)

    def on_view_mode_changed(self, mode: str) -> None:
        """Enregistre les changements d'affichage de l'explorateur."""
        self.model.record_action(f"view_mode:{mode}")

    def on_toggle_metadata(self, already_toggled: bool = False) -> None:
        """Bascule l'affichage des métadonnées dans la vue principale."""
        if not already_toggled and hasattr(self.view, "toggle_metadata_visibility"):
            self.view.toggle_metadata_visibility()
        self.model.record_action("metadata_toggle")
        self._update_timecode(self._current_video_path())

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _show_video(self, item: MediaItem) -> None:
        self._current_duration = self._probe_duration(item.path)
        payload = {
            "name": item.name,
            "path": str(item.path),
            "metadata": {
                **item.metadata,
                "time": self._format_duration(0.0, self._current_duration),
                "duration": self._format_duration(self._current_duration, self._current_duration),
                "duration_seconds": self._current_duration,
            },
        }
        frame, histogram = self._load_preview_frame(item.path)
        self.view.update_video_player(payload, frame=frame)
        # Timeline setup
        if hasattr(self.view, "video_player"):
            if hasattr(self.view.video_player, "set_duration_seconds"):
                self.view.video_player.set_duration_seconds(self._current_duration)
            if hasattr(self.view.video_player, "set_markers"):
                markers = item.metadata.get("markers") if item.metadata else None
                self.view.video_player.set_markers(markers or [])
            if hasattr(self.view.video_player, "set_export_range"):
                self.view.video_player.set_export_range(None, None)
        self._last_export_range = None
        if histogram:
            self.view.update_histogram(histogram)
        else:
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
        # Ajuster l'histogramme avec les corrections actuelles
        if hasattr(self.view, "update_histogram"):
            self.view.update_histogram(self.view._build_histogram_payload(corrections) if hasattr(self.view, "_build_histogram_payload") else None)

    def _register_processing_action(self, action: str, details: dict | None = None) -> None:
        detail_str = None
        if details:
            detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        # Historique simple (préserve les assertions de tests existants)
        self.model.record_action(action)
        current = self.model.get_selected_video()
        message = f"{action} triggered"
        if current:
            message += f" for {current.name}"
        if detail_str:
            message += f" ({detail_str})"
        self.view.show_message(message, "info")

    # ------------------------------------------------------------------ #
    # Frame + histogram helpers
    # ------------------------------------------------------------------ #
    def _load_preview_frame(self, path: Path) -> tuple[Optional[np.ndarray], Optional[dict]]:
        """Charge le premier frame d'une vidéo et calcule l'histogramme."""
        cap = cv2.VideoCapture(str(path))
        # Positionner à 10% pour un aperçu plus représentatif
        total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        if total_frames > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(total_frames * 0.1))
        ok, frame = cap.read()
        cap.release()
        if not ok or frame is None:
            self.view.show_message(f"Impossible de lire la vidéo {path}", "warning")
            return None, None
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        histogram = self._compute_histogram(rgb)
        return rgb, histogram

    def _compute_histogram(self, rgb_frame: np.ndarray) -> dict:
        """Retourne les listes de bins pour R/G/B + densité moyenne."""
        channels = []
        for idx in range(3):
            hist = cv2.calcHist([rgb_frame], [idx], None, [256], [0, 256]).flatten()
            channels.append(hist.tolist())
        density = [int((r + g + b) / 3) for r, g, b in zip(*channels)]
        return {
            "data_r": channels[0],
            "data_g": channels[1],
            "data_b": channels[2],
            "data_density": density,
        }

    def _frame_at_position(self, path: Path, position: int) -> Optional[np.ndarray]:
        """Récupère un frame à une position normalisée 0-1000."""
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            return None
        total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        target_idx = int(max(0, min(1000, position)) / 1000.0 * max(1, total_frames - 1))
        cap.set(cv2.CAP_PROP_POS_FRAMES, target_idx)
        ok, frame = cap.read()
        cap.release()
        if not ok or frame is None:
            return None
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def _colorize_thumbnails(self, payload: list[dict]) -> None:
        """Calcule une couleur moyenne par vidéo pour une miniature plus parlante."""
        for video in payload:
            path = Path(video.get("path", ""))
            if not path.is_file():
                continue
            cap = cv2.VideoCapture(str(path))
            if not cap.isOpened():
                continue
            total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
            if total_frames > 0:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(total_frames * 0.1))
            ok, frame = cap.read()
            cap.release()
            if not ok or frame is None:
                continue
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mean_color = rgb.reshape(-1, 3).mean(axis=0)
            r, g, b = [int(x) for x in mean_color]
            video["thumbnail_color"] = f"#{r:02x}{g:02x}{b:02x}"

    def _format_duration(self, value: float, total: float | None = None) -> str:
        """Formate un temps en mm:ss ou hh:mm:ss."""
        total_seconds = int(round(value))
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def _update_timecode(self, path: Path | None) -> None:
        if not path:
            return
        elapsed = self._current_playback_seconds(path, self._current_duration)
        time_str = self._format_duration(elapsed, self._current_duration)
        duration_str = self._format_duration(self._current_duration, self._current_duration)
        if hasattr(self.view, "video_player") and hasattr(self.view.video_player, "update_metadata"):
            self.view.video_player.update_metadata(
                time=time_str,
                duration=duration_str,
                duration_seconds=self._current_duration,
            )

    # ------------------------------------------------------------------ #
    # Dialog helpers
    # ------------------------------------------------------------------ #
    def _prompt_capture_name(self) -> str | None:
        """Boîte de dialogue pour nommer une capture d'écran."""
        if self._auto_accept_dialogs():
            return "capture"
        name, ok = QInputDialog.getText(
            self.view,
            "Nommer la capture",
            "Nom de la capture :",
            text="capture",
        )
        return name.strip() if ok and name.strip() else None

    # ------------------------------------------------------------------ #
    # Campaign auto-load
    # ------------------------------------------------------------------ #
    def _maybe_autoload_campaign(self) -> None:
        """Charge automatiquement les vidéos de la campagne ouverte si possible."""
        if not self.campaign_model:
            return
        target_name = self.campaign_model.last_opened
        if target_name is None and self.campaign_model.campaigns():
            target_name = self.campaign_model.campaigns()[0].name
        if not target_name:
            return

        base_dir = os.environ.get("KOSMOS_CAMPAIGNS_DIR")
        try:
            directory = self.campaign_model.resolve_campaign_path(target_name, base_dir)
        except Exception as exc:
            self.view.show_message(f"Impossible de résoudre la campagne '{target_name}': {exc}", "error")
            return

        if directory.is_dir():
            self.load_directory(directory)
        else:
            self.view.show_message(f"Dossier de campagne introuvable: {directory}", "warning")

    def _prompt_recording_range(self) -> tuple[int, int] | None:
        """Boîte de dialogue pour saisir le début et la fin d'un enregistrement."""
        if self._auto_accept_dialogs():
            return 0, 30

        dialog = QDialog(self.view)
        dialog.setWindowTitle("Enregistrement vidéo")
        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        start_spin = QSpinBox()
        start_spin.setRange(0, 36000)
        start_spin.setValue(0)
        end_spin = QSpinBox()
        end_spin.setRange(0, 36000)
        end_spin.setValue(30)
        form.addRow("Début (s)", start_spin)
        form.addRow("Fin (s)", end_spin)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            start = start_spin.value()
            end = max(end_spin.value(), start)
            return start, end
        return None

    def _prompt_short_name(self) -> str | None:
        """Boîte de dialogue pour nommer le short de 30s."""
        if self._auto_accept_dialogs():
            return "short_30s"

        name, ok = QInputDialog.getText(
            self.view,
            "Créer un short (30s)",
            "Nom du short :",
            text="short_30s",
        )
        return name.strip() if ok and name.strip() else None

    # ------------------------------------------------------------------ #
    # Export helpers
    # ------------------------------------------------------------------ #
    def _auto_accept_dialogs(self) -> bool:
        """Permet aux tests (CI) de bypasser les boîtes de dialogue."""
        return bool(os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("CI"))

    def _current_video_path(self) -> Optional[Path]:
        current = self.model.get_selected_video()
        if not current:
            self.view.show_message("Aucune vidéo sélectionnée.", "warning")
            return None
        return current.path

    def _probe_duration(self, path: Path) -> float:
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            return 0.0
        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        cap.release()
        if fps <= 0:
            return 0.0
        return float(frames) / float(fps)

    def _current_playback_seconds(self, path: Path, duration: float | None = None) -> float:
        """Convertit la position normalisée (0-1000) en secondes réelles."""
        dur = duration if duration is not None else self._probe_duration(path)
        if dur <= 0:
            return 0.0
        ratio = self.model.get_playback_position() / 1000.0
        return max(0.0, min(dur, ratio * dur))

    def _set_export_range_visual(self, start_s: float, end_s: float) -> None:
        """Met à jour la zone d'export affichée sur la timeline."""
        if self._current_duration <= 0:
            return
        start_norm = int(max(0.0, min(start_s, self._current_duration)) / self._current_duration * 1000)
        end_norm = int(max(0.0, min(end_s, self._current_duration)) / self._current_duration * 1000)
        if hasattr(self.view, "video_player") and hasattr(self.view.video_player, "set_export_range"):
            self.view.video_player.set_export_range(start_norm, end_norm)
        self._last_export_range = (start_norm, end_norm)

    def _export_screenshot(self, path: Path, name: str) -> bool:
        duration = self._probe_duration(path)
        second = self._current_playback_seconds(path, duration)
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            self.view.show_message(f"Impossible d'ouvrir la vidéo pour capture: {path}", "error")
            return False
        cap.set(cv2.CAP_PROP_POS_MSEC, second * 1000.0)
        ok, frame = cap.read()
        cap.release()
        if not ok or frame is None:
            self.view.show_message("Lecture du frame échouée pour la capture.", "error")
            return False
        dest = path.parent / f"{Path(name).stem}.png"
        cv2.imwrite(str(dest), frame)
        self.view.show_message(f"Capture enregistrée: {dest}", "success")
        return True

    def _export_subclip(self, path: Path, start: float, end: float, suffix: str) -> bool:
        duration = self._probe_duration(path)
        if duration > 0:
            start = max(0.0, min(start, duration))
            end = max(start, min(end, duration))
        if end - start <= 0:
            self.view.show_message("Durée d'extraction invalide.", "warning")
            return False
        output = path.parent / f"{path.stem}_{suffix}.mp4"
        try:
            ffmpeg_extract_subclip(str(path), start, end, targetname=str(output))
        except Exception as exc:
            self.view.show_message(f"Erreur d'extraction vidéo: {exc}", "error")
            return False
        self.view.show_message(f"Segment exporté: {output} ({start:.2f}s → {end:.2f}s)", "success")
        return True
