"""
Extract frames from videos into train/val image folders.

Default paths target the provided dataset:
  --videos-root /mnt/c/Users/USER/Downloads/Data_Kosmos/extracted/Documentation by Olivier
  --output-root /mnt/c/Users/USER/Downloads/Data_Kosmos
It creates:
  {output_root}/train/images
  {output_root}/val/images

Masks are not created; this just prepares frames for later annotation.
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Iterable, Tuple

import cv2
from tqdm import tqdm


def list_videos(root: Path) -> list[Path]:
    videos = sorted(root.rglob("*.mp4"))
    if not videos:
        raise FileNotFoundError(f"No videos found under {root}")
    return videos


def ensure_dirs(output_root: Path) -> Tuple[Path, Path]:
    train_dir = output_root / "train" / "images"
    val_dir = output_root / "val" / "images"
    train_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)
    return train_dir, val_dir


def extract_video(
    video_path: Path,
    dest_dir: Path,
    target_fps: float,
    max_frames: int | None = None,
) -> int:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open {video_path}")

    input_fps = cap.get(cv2.CAP_PROP_FPS) or 0
    if input_fps <= 0:
        input_fps = target_fps  # fallback to requested fps
    frame_interval = max(int(round(input_fps / target_fps)), 1)

    saved = 0
    frame_idx = 0
    stem = video_path.stem
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            out_name = f"{stem}_f{frame_idx:06d}.jpg"
            out_path = dest_dir / out_name
            cv2.imwrite(str(out_path), frame)
            saved += 1
            if max_frames is not None and saved >= max_frames:
                break
        frame_idx += 1
    cap.release()
    return saved


def split_videos(videos: list[Path], val_ratio: float, seed: int) -> Tuple[list[Path], list[Path]]:
    rng = random.Random(seed)
    rng.shuffle(videos)
    val_count = max(1, int(len(videos) * val_ratio))
    val_videos = videos[:val_count]
    train_videos = videos[val_count:]
    return train_videos, val_videos


def process(
    videos_root: Path,
    output_root: Path,
    target_fps: float,
    val_ratio: float,
    max_frames_per_video: int | None,
    seed: int,
) -> None:
    videos = list_videos(videos_root)
    train_dir, val_dir = ensure_dirs(output_root)
    train_videos, val_videos = split_videos(videos, val_ratio, seed)

    print(f"Found {len(videos)} videos. Train: {len(train_videos)}, Val: {len(val_videos)}")
    for split_name, subset, dest_dir in [
        ("train", train_videos, train_dir),
        ("val", val_videos, val_dir),
    ]:
        print(f"Processing {split_name} videos into {dest_dir}")
        for v in tqdm(subset, desc=f"{split_name}"):
            saved = extract_video(v, dest_dir, target_fps, max_frames_per_video)
            if saved == 0:
                print(f"Warning: no frames saved from {v}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract frames to train/val image folders.")
    parser.add_argument(
        "--videos-root",
        type=Path,
        default=Path("/mnt/c/Users/USER/Downloads/Data_Kosmos/extracted/Documentation by Olivier"),
        help="Root directory containing MP4 files (searches recursively).",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("/mnt/c/Users/USER/Downloads/Data_Kosmos"),
        help="Destination root; train/images and val/images will be created here.",
    )
    parser.add_argument("--fps", type=float, default=1.0, help="Target extraction FPS.")
    parser.add_argument("--val-ratio", type=float, default=0.2, help="Portion of videos for validation.")
    parser.add_argument("--max-frames-per-video", type=int, default=None, help="Optional cap per video.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for train/val split.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    process(
        videos_root=args.videos_root,
        output_root=args.output_root,
        target_fps=args.fps,
        val_ratio=args.val_ratio,
        max_frames_per_video=args.max_frames_per_video,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
