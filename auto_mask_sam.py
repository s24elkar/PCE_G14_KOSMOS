"""
Generate automatic masks with Segment Anything (SAM) and save binary PNGs.

Usage example (PowerShell one-liner):
python auto_mask_sam.py --images "C:\\Users\\USER\\Downloads\\Data_Kosmos\\train\\images" --output "C:\\Users\\USER\\Downloads\\Data_Kosmos\\train\\masks" --checkpoint "C:\\path\\to\\sam_vit_b.pth" --min-area 500 --max-masks 3

Requirements:
- torch, torchvision
- opencv-python
- segment-anything (pip install git+https://github.com/facebookresearch/segment-anything.git)
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import cv2
import numpy as np
import torch
from tqdm import tqdm


def load_sam(checkpoint: Path, model_type: str = "vit_b"):
    from segment_anything import SamAutomaticMaskGenerator, sam_model_registry

    # SAM registry keys are typically "vit_b", "vit_l", "vit_h"
    key = model_type
    if key.startswith("sam_"):
        key = key[len("sam_") :]
    if key not in sam_model_registry:
        raise KeyError(f"Unknown SAM model type '{model_type}', available: {list(sam_model_registry.keys())}")
    sam = sam_model_registry[key](checkpoint=checkpoint)
    sam.to("cuda" if torch.cuda.is_available() else "cpu")
    generator = SamAutomaticMaskGenerator(
        sam,
        points_per_side=16,
        pred_iou_thresh=0.88,
        stability_score_thresh=0.9,
        crop_n_layers=1,
        crop_n_points_downscale_factor=2,
        min_mask_region_area=0,  # we filter manually
    )
    return generator


def filter_masks(masks: List[dict], min_area: int, max_masks: int) -> List[dict]:
    masks = [m for m in masks if m["area"] >= min_area]
    masks.sort(key=lambda m: m["area"], reverse=True)
    return masks[:max_masks]


def save_mask(mask: np.ndarray, path: Path) -> None:
    # mask is boolean or 0/1; save as 0/255 uint8
    mask_uint8 = (mask.astype(np.uint8)) * 255
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), mask_uint8)


def process_images(
    images_dir: Path,
    output_dir: Path,
    checkpoint: Path,
    min_area: int,
    max_masks: int,
    model_type: str,
) -> None:
    generator = load_sam(checkpoint, model_type=model_type)
    image_paths = sorted(
        [*images_dir.glob("*.jpg"), *images_dir.glob("*.jpeg"), *images_dir.glob("*.png")]
    )
    if not image_paths:
        raise FileNotFoundError(f"No images found in {images_dir}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}. Processing {len(image_paths)} images.")

    for img_path in tqdm(image_paths, desc="SAM auto masks"):
        image = cv2.cvtColor(cv2.imread(str(img_path)), cv2.COLOR_BGR2RGB)
        masks = generator.generate(image)
        masks = filter_masks(masks, min_area=min_area, max_masks=max_masks)
        if not masks:
            continue
        # combine selected masks into a single binary mask
        combined = np.zeros(image.shape[:2], dtype=np.uint8)
        for m in masks:
            combined = np.logical_or(combined, m["segmentation"])
        out_path = output_dir / (img_path.stem + ".png")
        save_mask(combined, out_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate masks with SAM.")
    parser.add_argument("--images", type=Path, required=True, help="Folder with input images (jpg/png).")
    parser.add_argument("--output", type=Path, required=True, help="Folder to save binary masks.")
    parser.add_argument("--checkpoint", type=Path, required=True, help="Path to SAM checkpoint (sam_vit_b.pth).")
    parser.add_argument(
        "--min-area",
        type=int,
        default=500,
        help="Minimum mask area (pixels) to keep.",
    )
    parser.add_argument(
        "--max-masks",
        type=int,
        default=3,
        help="Maximum number of largest masks to keep per image.",
    )
    parser.add_argument(
        "--model-type",
        type=str,
        default="vit_b",
        choices=["vit_b", "vit_l", "vit_h"],
        help="SAM model variant matching the checkpoint.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    process_images(
        images_dir=args.images,
        output_dir=args.output,
        checkpoint=args.checkpoint,
        min_area=args.min_area,
        max_masks=args.max_masks,
        model_type=args.model_type,
    )


if __name__ == "__main__":
    main()
