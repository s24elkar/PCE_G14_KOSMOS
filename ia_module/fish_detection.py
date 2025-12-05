"""
YOLO-based fish detection helpers.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional

import cv2
import numpy as np
from ultralytics import YOLO

DEFAULT_WEIGHTS = Path(__file__).parent / "checkpoints" / "yolo_fish.pt"
MODEL: Optional[YOLO] = None


def load_model(model_path: Optional[str | Path] = None) -> YOLO:
    """Load a YOLOv8/YOLOv10 model on CPU."""
    global MODEL
    if model_path:
        weights = Path(model_path)
    else:
        # Prefer configured default, otherwise try a common fallback (best.pt) in the same folder.
        default_dir = DEFAULT_WEIGHTS.parent
        default_dir.mkdir(parents=True, exist_ok=True)
        if DEFAULT_WEIGHTS.exists():
            weights = DEFAULT_WEIGHTS
        else:
            alt = default_dir / "best.pt"
            if alt.exists():
                weights = alt
            else:
                raise FileNotFoundError(f"Fichier de poids YOLO introuvable: {DEFAULT_WEIGHTS} (ni {alt})")
    MODEL = YOLO(str(weights))
    MODEL.to("cpu")
    return MODEL


def _scale_for_inference(frame: np.ndarray, max_side: int = 640) -> tuple[np.ndarray, float, float]:
    """Resize frame for faster inference, returning scale factors to original size."""
    if frame.ndim == 2:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    h, w = frame.shape[:2]
    ratio = min(1.0, float(max_side) / float(max(h, w)))
    if ratio >= 1.0:
        return frame, 1.0, 1.0
    new_w = max(1, int(w * ratio))
    new_h = max(1, int(h * ratio))
    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    return resized, w / float(new_w), h / float(new_h)


def detect_fish(frame: np.ndarray) -> List[dict]:
    """
    Run YOLO detection on a single frame.

    Returns a list of dicts with keys: bbox (x1, y1, x2, y2), cls, confidence, name.
    """
    global MODEL
    if MODEL is None:
        load_model()

    if frame is None or frame.size == 0:
        return []
    if frame.ndim == 2:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

    infer_frame, scale_x, scale_y = _scale_for_inference(frame)
    results = MODEL(infer_frame, verbose=False, device="cpu")
    results_seq = results if isinstance(results, (list, tuple)) else [results]
    names = getattr(MODEL, "names", {}) or {}

    detections: List[dict] = []
    for res in results_seq:
        res_names = getattr(res, "names", None) or names
        boxes = getattr(res, "boxes", None)
        if boxes is None:
            continue
        for box in boxes:
            xyxy = box.xyxy[0].tolist()
            cls_idx = int(box.cls.item()) if hasattr(box.cls, "item") else int(box.cls)
            conf = float(box.conf.item()) if hasattr(box.conf, "item") else float(box.conf)
            name = res_names.get(cls_idx, str(cls_idx)) if isinstance(res_names, dict) else str(cls_idx)
            x1, y1, x2, y2 = xyxy
            detections.append(
                {
                    "bbox": (x1 * scale_x, y1 * scale_y, x2 * scale_x, y2 * scale_y),
                    "cls": cls_idx,
                    "confidence": conf,
                    "name": name,
                }
            )
    return detections


def process_video(
    input_path: str | Path,
    output_path: str | Path,
    progress_callback: Optional[Callable[[int], None]] = None,
    preview_callback: Optional[Callable[[np.ndarray], None]] = None,
) -> str:
    """Process a video, drawing detections and streaming frames to the preview callback."""
    global MODEL
    if MODEL is None:
        load_model()

    input_path = str(input_path)
    output_path = str(output_path)

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError(f"Impossible d'ouvrir la vidéo: {input_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

    processed = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break
            if frame.ndim == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

            detections = detect_fish(frame)
            for det in detections:
                x1, y1, x2, y2 = det["bbox"]
                species_name = det["name"]
                conf_pct = det["confidence"] * 100.0
                label = f"{species_name} {conf_pct:.1f}%"
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    label,
                    (int(x1), int(max(y1 - 10, 0))),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA,
                )

            writer.write(frame)

            processed += 1
            if preview_callback:
                preview_callback(frame.copy())
            if progress_callback:
                pct = int(processed * 100 / total_frames)
                progress_callback(min(pct, 100))
    finally:
        cap.release()
        writer.release()

    if progress_callback:
        progress_callback(100)

    return output_path
