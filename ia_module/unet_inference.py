"""
Inference helpers for the milesial/Pytorch-UNet model.

This module keeps the UNet definition local so we do not have to clone the
external repository at runtime. The default weights path points to
``ia_module/checkpoints/unet_carvana_scale1_epoch5.pth`` – drop the pretrained
file there to use the official weights.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Optional

import cv2
import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except ImportError as exc:  # pragma: no cover - handled at runtime
    torch = None

    class _NNStub:
        Module = object

    nn = _NNStub()
    F = None
    _torch_import_error = exc
else:
    _torch_import_error = None


# ---------------------------------------------------------------------------
# Model definition (mirrors milesial/Pytorch-UNet)
# ---------------------------------------------------------------------------

class DoubleConv(nn.Module):
    """(convolution => ReLU) * 2"""

    def __init__(self, in_channels: int, out_channels: int, mid_channels: Optional[int] = None):
        super().__init__()
        if mid_channels is None:
            mid_channels = out_channels
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, mid_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(mid_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(mid_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.double_conv(x)


class Down(nn.Module):
    """Downscaling with maxpool then double conv"""

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.maxpool_conv = nn.Sequential(
            nn.MaxPool2d(2),
            DoubleConv(in_channels, out_channels),
        )

    def forward(self, x):
        return self.maxpool_conv(x)


class Up(nn.Module):
    """Upscaling then double conv"""

    def __init__(self, in_channels: int, out_channels: int, bilinear: bool = True):
        super().__init__()

        # if bilinear, use the normal convolutions to reduce the number of channels
        if bilinear:
            self.up = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=True)
            self.conv = DoubleConv(in_channels, out_channels, in_channels // 2)
        else:
            self.up = nn.ConvTranspose2d(in_channels, in_channels // 2, kernel_size=2, stride=2)
            self.conv = DoubleConv(in_channels, out_channels)

    def forward(self, x1, x2):
        x1 = self.up(x1)
        # input is CHW
        diff_y = x2.size()[2] - x1.size()[2]
        diff_x = x2.size()[3] - x1.size()[3]

        x1 = F.pad(x1, [diff_x // 2, diff_x - diff_x // 2, diff_y // 2, diff_y - diff_y // 2])
        x = torch.cat([x2, x1], dim=1)
        return self.conv(x)


class OutConv(nn.Module):
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=1)

    def forward(self, x):
        return self.conv(x)


class UNet(nn.Module):
    def __init__(self, n_channels: int = 3, n_classes: int = 1, bilinear: bool = True):
        super().__init__()
        self.n_channels = n_channels
        self.n_classes = n_classes
        self.bilinear = bilinear

        self.inc = DoubleConv(n_channels, 64)
        self.down1 = Down(64, 128)
        self.down2 = Down(128, 256)
        self.down3 = Down(256, 512)
        factor = 2 if bilinear else 1
        self.down4 = Down(512, 1024 // factor)
        self.up1 = Up(1024, 512 // factor, bilinear)
        self.up2 = Up(512, 256 // factor, bilinear)
        self.up3 = Up(256, 128 // factor, bilinear)
        self.up4 = Up(128, 64, bilinear)
        self.outc = OutConv(64, n_classes)

    def forward(self, x):
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        x5 = self.down4(x4)
        x = self.up1(x5, x4)
        x = self.up2(x, x3)
        x = self.up3(x, x2)
        x = self.up4(x, x1)
        logits = self.outc(x)
        return logits


# ---------------------------------------------------------------------------
# Inference helpers
# ---------------------------------------------------------------------------

if torch:
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
else:
    DEVICE = "cpu"
DEFAULT_WEIGHTS = Path(__file__).parent / "checkpoints" / "unet_carvana_scale1_epoch5.pth"
MODEL: Optional[nn.Module] = None


def _ensure_torch():
    if torch is None:
        raise ImportError(
            "PyTorch is required for IA processing. Install torch (CPU build is fine) before launching."
        ) from _torch_import_error


def load_unet_model(weights_path: Optional[str | Path] = None) -> nn.Module:
    """Load the pretrained UNet weights (or random init if file missing)."""
    _ensure_torch()
    global MODEL

    model = UNet(n_channels=3, n_classes=1, bilinear=True)

    weights_file = Path(weights_path) if weights_path else DEFAULT_WEIGHTS
    weights_file.parent.mkdir(parents=True, exist_ok=True)
    if weights_file.exists():
        state = torch.load(weights_file, map_location="cpu")
        if isinstance(state, dict) and "state_dict" in state:
            state = state["state_dict"]
        try:
            model.load_state_dict(state)
            print(f"✅ UNet weights chargés depuis {weights_file}")
        except RuntimeError as exc:
            print(f"⚠️ Impossible de charger strictement les poids ({exc}). Continuer avec init aléatoire.")
    else:
        print(f"⚠️ Fichier de poids introuvable: {weights_file}. Le modèle utilisera des poids initiaux.")

    model.to(DEVICE)
    model.eval()
    MODEL = model
    return model


def _prepare_tensor(frame: np.ndarray) -> tuple[torch.Tensor, tuple[int, int], np.ndarray]:
    """Convert BGR frame to tensor and pad to multiples of 16."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, _ = rgb.shape
    div = 16
    target_h = int(math.ceil(h / div) * div)
    target_w = int(math.ceil(w / div) * div)
    padded = cv2.copyMakeBorder(
        rgb, 0, target_h - h, 0, target_w - w, cv2.BORDER_REFLECT_101
    )
    tensor = torch.from_numpy(padded).float().permute(2, 0, 1) / 255.0
    tensor = tensor.unsqueeze(0).to(DEVICE)
    return tensor, (h, w), padded


def run_unet_on_frame(frame: np.ndarray) -> np.ndarray:
    """
    Apply UNet segmentation mask to a single frame.

    Args:
        frame: OpenCV BGR frame.
    Returns:
        Processed BGR frame.
    """
    _ensure_torch()
    global MODEL
    if MODEL is None:
        load_unet_model()

    if frame is None or frame.size == 0:
        raise ValueError("Frame is empty.")
    if frame.ndim == 2:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

    with torch.no_grad():
        tensor, (orig_h, orig_w), padded = _prepare_tensor(frame)
        logits = MODEL(tensor)
        probs = torch.sigmoid(logits)
        mask = probs.squeeze().cpu().numpy()

        if mask.ndim == 2:
            mask = mask[..., None]

        mask = cv2.resize(mask, (padded.shape[1], padded.shape[0]))
        mask = mask[:orig_h, :orig_w, :]
        mask_3c = np.repeat(mask, 3, axis=2)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float32)
        enhanced = rgb * mask_3c
        enhanced = np.clip(enhanced, 0, 255).astype(np.uint8)

        return cv2.cvtColor(enhanced, cv2.COLOR_RGB2BGR)


def process_video(
    input_path: str | Path,
    output_path: str | Path,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> str:
    """
    Run UNet inference on every frame of the input video.

    Args:
        input_path: Source video.
        output_path: Destination video to write.
        progress_callback: Optional callable receiving an int percentage.
    Returns:
        The output path as string.
    """
    _ensure_torch()
    global MODEL
    if MODEL is None:
        load_unet_model()

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
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    processed = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break
            if frame.ndim == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            out_frame = run_unet_on_frame(frame)
            writer.write(out_frame)

            processed += 1
            if progress_callback:
                pct = int(processed * 100 / total_frames)
                progress_callback(min(pct, 100))
    finally:
        cap.release()
        writer.release()

    if progress_callback:
        progress_callback(100)

    return output_path
