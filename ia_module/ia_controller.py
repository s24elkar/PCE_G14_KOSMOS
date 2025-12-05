"""
Controller for the IA tab.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal

from ia_module import fish_detection, unet_inference


class IAKosmosController(QObject):
    """Controller responsible for IA processing orchestration."""

    navigation_demandee = pyqtSignal(str)
    video_selectionnee = pyqtSignal(object)
    modele_charge = pyqtSignal(bool, str)
    modele_fish_charge = pyqtSignal(bool, str)

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.modele_ok = False
        self.fish_modele_ok = False
        self.weights_path: Optional[Path] = None
        self.fish_weights_path: Optional[Path] = Path(__file__).parent / "checkpoints" / "yolo_fish.pt"

    def obtenir_videos(self):
        return self.model.obtenir_videos()

    def selectionner_video(self, nom_video: str):
        video = self.model.selectionner_video(nom_video)
        if video:
            self.video_selectionnee.emit(video)
        return video

    def charger_modele(self, chemin_poids: Optional[str] = None) -> bool:
        try:
            self.weights_path = Path(chemin_poids) if chemin_poids else None
            unet_inference.load_unet_model(self.weights_path)
            self.modele_ok = True
            self.modele_charge.emit(True, "Modèle U-Net prêt")
            return True
        except Exception as exc:  # pragma: no cover - runtime feedback
            self.modele_ok = False
            self.modele_charge.emit(False, str(exc))
            print(f"❌ Chargement modèle IA: {exc}")
            return False

    def traiter_video(self, entree: str, sortie: str, progress_cb=None) -> str:
        if not self.modele_ok:
            self.charger_modele(self.weights_path)
        return unet_inference.process_video(entree, sortie, progress_callback=progress_cb)

    def get_angle_seek_times(self, nom_video: str):
        """Reuse the same seek time computation as the tri view."""
        return self.model.get_angle_event_times(nom_video)

    def get_output_path(self, input_path: str) -> str:
        base = Path(input_path)
        return str(base.with_name(f"{base.stem}_ia{base.suffix}"))

    # ------------------------------------------------------------------
    # Fish detection (YOLO)
    # ------------------------------------------------------------------

    def load_fish_model(self, chemin_poids: Optional[str] = None) -> bool:
        try:
            self.fish_weights_path = Path(chemin_poids) if chemin_poids else self.fish_weights_path
            fish_detection.load_model(self.fish_weights_path)
            self.fish_modele_ok = True
            self.modele_fish_charge.emit(True, "Modèle YOLO chargé")
            return True
        except Exception as exc:  # pragma: no cover - runtime feedback
            self.fish_modele_ok = False
            self.modele_fish_charge.emit(False, str(exc))
            print(f"❌ Chargement modèle détection poissons: {exc}")
            return False

    def get_fish_output_path(self, input_path: str) -> str:
        base = Path(input_path)
        output_dir = Path("processed")
        output_dir.mkdir(parents=True, exist_ok=True)
        return str(output_dir / f"{base.stem}_fish_detected.mp4")

    def run_fish_detection(self, input_video_path: str, progress_cb=None, preview_cb=None) -> str:
        if not self.fish_modele_ok:
            self.load_fish_model(self.fish_weights_path)
        output_path = self.get_fish_output_path(input_video_path)
        return fish_detection.process_video(
            input_video_path, output_path, progress_callback=progress_cb, preview_callback=preview_cb
        )
