import argparse
import sys
from pathlib import Path
from typing import Optional

import cv2
import matplotlib.pyplot as plt
import numpy as np

if __package__ in (None, ""):
    # Autorise l'exécution directe du script sans installation du package.
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from kosmos_processing.algos_correction import (  # type: ignore
        annotate_detections,
        atm_calculation,
        denoise_image,
        detect_moving_subjects,
        init_motion_detector,
        process_image_dehaze,
        tenengrad_contrast,
    )
else:
    from .algos_correction import (
        annotate_detections,
        atm_calculation,
        denoise_image,
        detect_moving_subjects,
        init_motion_detector,
        process_image_dehaze,
        tenengrad_contrast,
    )

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def load_frame(path: Path, frame_index: int = 0) -> np.ndarray:
    if path.suffix.lower() in IMAGE_EXTENSIONS:
        frame = cv2.imread(str(path))
        if frame is None:
            raise ValueError(f"Impossible de charger l'image à {path}")
        return frame

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError(f"Impossible d'ouvrir la vidéo à {path}")

    if frame_index > 0:
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

    ret, frame = capture.read()
    capture.release()
    if not ret or frame is None:
        raise ValueError(f"Impossible de lire la frame {frame_index} depuis {path}.")
    return frame


def resolve_default_path(default: str) -> Optional[Path]:
    path = Path(default)
    if path.exists():
        return path
    candidates = sorted(Path(".").glob("**/*.mp4"))
    return candidates[0] if candidates else None


def main():
    parser = argparse.ArgumentParser(description="Visualise la chaîne de correction KOSMOS.")
    parser.add_argument(
        "image",
        nargs="?",
        default=None,
        help="Chemin vers l'image ou la vidéo à analyser. Par défaut, tente data/sample.jpg puis cherche un MP4.",
    )
    parser.add_argument(
        "--frame",
        type=int,
        default=0,
        help="Indice de frame à extraire pour une vidéo (défaut: 0).",
    )
    args = parser.parse_args()

    if args.image is not None:
        image_path = Path(args.image)
    else:
        resolved = resolve_default_path("data/sample.jpg")
        if resolved is None:
            raise FileNotFoundError(
                "Aucun fichier fourni, data/sample.jpg introuvable, et aucun MP4 détecté dans le dossier."
            )
        image_path = resolved

    if not image_path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {image_path.resolve()}")

    frame = load_frame(image_path, frame_index=args.frame)
    atm = atm_calculation(frame)
    dehazed = process_image_dehaze(frame, atm, window=21, omega=0.7)
    denoised = denoise_image(dehazed, method="nlm", h=12)

    detector = init_motion_detector()
    detections = detect_moving_subjects(denoised, detector)
    annotated = annotate_detections(denoised, detections)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes[0, 0].imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    axes[0, 0].set_title("Original")
    axes[0, 1].imshow(cv2.cvtColor(dehazed, cv2.COLOR_BGR2RGB))
    axes[0, 1].set_title("Dehazed")
    axes[1, 0].imshow(cv2.cvtColor(denoised, cv2.COLOR_BGR2RGB))
    axes[1, 0].set_title("Denoised")
    axes[1, 1].imshow(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB))
    axes[1, 1].set_title(f"Detections • Tenengrad={tenengrad_contrast(annotated):.1f}")
    for ax in axes.ravel():
        ax.axis("off")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
