"""
Lightweight wrapper around the DeepSeaEnhance multi-head U-Net model.

The wrapper loads the configuration and checkpoint files produced by the
DeepSeaEnhance training pipeline and exposes a simple ``enhance`` method that
accepts BGR ``numpy`` frames (as returned by OpenCV) and returns restored
images, segmentation masks, and optional regression outputs.

The implementation copies the model definition to avoid depending on the
original DeepSeaEnhance repository as a Python package while still keeping the
runtime self-contained for the Kosmos desktop application.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import yaml
from torchvision import models

__all__ = ["DeepSeaEnhancer", "DeepSeaEnhancerConfig", "DeepSeaEnhancerResult"]


# -----------------------------------------------------------------------------
# Model definition (adapted from DeepSeaEnhance/src/kosmos_learning/models/unet.py)
# -----------------------------------------------------------------------------

def _init_weights(module: nn.Module) -> None:
    if isinstance(module, nn.Conv2d):
        nn.init.kaiming_normal_(module.weight, mode="fan_out", nonlinearity="relu")
        if module.bias is not None:
            nn.init.zeros_(module.bias)
    elif isinstance(module, nn.BatchNorm2d):
        nn.init.ones_(module.weight)
        nn.init.zeros_(module.bias)
    elif isinstance(module, nn.Linear):
        nn.init.normal_(module.weight, 0, 0.01)
        nn.init.zeros_(module.bias)


class ConvBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, *, use_batchnorm: bool = True) -> None:
        super().__init__()
        layers: List[nn.Module] = [
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=not use_batchnorm),
        ]
        if use_batchnorm:
            layers.append(nn.BatchNorm2d(out_channels))
        layers.append(nn.ReLU(inplace=True))
        layers.append(nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=not use_batchnorm))
        if use_batchnorm:
            layers.append(nn.BatchNorm2d(out_channels))
        layers.append(nn.ReLU(inplace=True))
        self.block = nn.Sequential(*layers)
        self.block.apply(_init_weights)

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # pragma: no cover - thin wrapper
        return self.block(x)


class DecoderBlock(nn.Module):
    def __init__(self, in_channels: int, skip_channels: int, out_channels: int) -> None:
        super().__init__()
        self.conv = ConvBlock(in_channels + skip_channels, out_channels)

    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:  # pragma: no cover - thin wrapper
        x = F.interpolate(x, size=skip.shape[2:], mode="bilinear", align_corners=False)
        x = torch.cat([x, skip], dim=1)
        return self.conv(x)


class MultiTaskUNet(nn.Module):
    """
    ResNet34 encoder U-Net with segmentation, restoration, and regression heads.
    """

    def __init__(
        self,
        *,
        in_channels: int = 3,
        num_classes: int = 6,
        regression_channels: int = 0,
        restoration_channels: int = 0,
        encoder_name: str = "resnet34",
        encoder_pretrained: bool = True,
        decoder_base_channels: int = 256,
    ) -> None:
        super().__init__()
        if encoder_name != "resnet34":
            raise ValueError("Currently only resnet34 encoder is supported.")

        weights = None
        if encoder_pretrained:
            try:
                weights = models.ResNet34_Weights.IMAGENET1K_V1  # type: ignore[attr-defined]
            except AttributeError:  # torchvision < 0.13 compatibility
                weights = "IMAGENET1K_V1"

        try:
            base_model = models.resnet34(weights=weights)
        except Exception:  # pragma: no cover - offline fallback
            base_model = models.resnet34(weights=None)

        if in_channels != 3:
            conv1 = nn.Conv2d(in_channels, 64, kernel_size=7, stride=2, padding=3, bias=False)
            with torch.no_grad():
                if encoder_pretrained and base_model.conv1.weight.shape[1] == 3:
                    conv1.weight[:, :3, :, :] = base_model.conv1.weight
                    if in_channels > 3:
                        nn.init.kaiming_normal_(conv1.weight[:, 3:, :, :], mode="fan_out", nonlinearity="relu")
            base_model.conv1 = conv1

        self.encoder = base_model
        self.encoder_layers = nn.ModuleList(
            [
                nn.Sequential(self.encoder.conv1, self.encoder.bn1, self.encoder.relu),
                nn.Sequential(self.encoder.maxpool, self.encoder.layer1),
                self.encoder.layer2,
                self.encoder.layer3,
                self.encoder.layer4,
            ]
        )

        encoder_channels = [64, 64, 128, 256, 512]
        self.center = ConvBlock(encoder_channels[-1], decoder_base_channels)

        decoder_channels = [
            decoder_base_channels,
            decoder_base_channels // 2,
            decoder_base_channels // 2,
            decoder_base_channels // 4,
        ]

        self.decoder_blocks = nn.ModuleList(
            [
                DecoderBlock(decoder_channels[0], encoder_channels[-2], decoder_channels[1]),
                DecoderBlock(decoder_channels[1], encoder_channels[-3], decoder_channels[2]),
                DecoderBlock(decoder_channels[2], encoder_channels[-4], decoder_channels[3]),
                DecoderBlock(decoder_channels[3], encoder_channels[-5], decoder_channels[3]),
            ]
        )

        self.final_conv = nn.Sequential(
            nn.Conv2d(decoder_channels[3], decoder_channels[3], kernel_size=3, padding=1),
            nn.BatchNorm2d(decoder_channels[3]),
            nn.ReLU(inplace=True),
        )

        self.segmentation_head: Optional[nn.Module] = None
        self.restoration_head: Optional[nn.Module] = None
        self.regression_head: Optional[nn.Module] = None

        if num_classes > 0:
            self.segmentation_head = nn.Conv2d(decoder_channels[3], num_classes, kernel_size=1)
            nn.init.xavier_uniform_(self.segmentation_head.weight)
            if self.segmentation_head.bias is not None:
                nn.init.zeros_(self.segmentation_head.bias)

        if restoration_channels > 0:
            self.restoration_head = nn.Sequential(
                nn.Conv2d(decoder_channels[3], restoration_channels, kernel_size=3, padding=1),
                nn.Sigmoid(),
            )
            self.restoration_head.apply(_init_weights)

        if regression_channels > 0:
            self.regression_head = nn.Sequential(
                nn.AdaptiveAvgPool2d(1),
                nn.Flatten(),
                nn.Linear(decoder_channels[3], decoder_channels[3] // 2),
                nn.ReLU(inplace=True),
                nn.Dropout(p=0.2),
                nn.Linear(decoder_channels[3] // 2, regression_channels),
            )
            self.regression_head.apply(_init_weights)

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        encoder_features: List[torch.Tensor] = []
        out = x
        for layer in self.encoder_layers:
            out = layer(out)
            encoder_features.append(out)

        bottleneck = self.center(encoder_features[-1])
        dec = bottleneck
        skip_features = encoder_features[:-1][::-1]
        for idx, decoder_block in enumerate(self.decoder_blocks):
            skip = skip_features[idx] if idx < len(skip_features) else skip_features[-1]
            dec = decoder_block(dec, skip)

        features = self.final_conv(dec)
        outputs: Dict[str, torch.Tensor] = {}

        if self.segmentation_head is not None:
            seg_logits = self.segmentation_head(features)
            seg_logits = F.interpolate(seg_logits, size=x.shape[2:], mode="bilinear", align_corners=False)
            outputs["segmentation"] = seg_logits

        if self.restoration_head is not None:
            rest = self.restoration_head(features)
            rest = F.interpolate(rest, size=x.shape[2:], mode="bilinear", align_corners=False)
            outputs["restoration"] = rest

        if self.regression_head is not None:
            outputs["regression"] = self.regression_head(features)

        outputs["features"] = features
        return outputs


# -----------------------------------------------------------------------------
# Public wrapper
# -----------------------------------------------------------------------------


@dataclass
class DeepSeaEnhancerConfig:
    """
    Configuration describing where to load the DeepSeaEnhance assets from.
    """

    config_path: Path
    checkpoint_path: Path
    device_override: Optional[str] = None


@dataclass
class DeepSeaEnhancerResult:
    """Container returned by :meth:`DeepSeaEnhancer.enhance`."""

    restored_bgr: List[np.ndarray] = field(default_factory=list)
    overlay_bgr: Optional[np.ndarray] = None
    mask: Optional[np.ndarray] = None
    regression: Optional[np.ndarray] = None
    meta: Dict[str, object] = field(default_factory=dict)


class DeepSeaEnhancer:
    """
    Convenience wrapper that mirrors the PyTorch inference path from
    DeepSeaEnhance's GUI utilities without pulling the whole package.
    """

    def __init__(
        self,
        *,
        config: Optional[DeepSeaEnhancerConfig] = None,
        root_hint: Optional[Path] = None,
        auto_prepare: bool = False,
    ) -> None:
        if config is None:
            root = self._discover_root(root_hint)
            config_path = root / "config" / "config.yaml"
            checkpoint_path = root / "weights" / "best_model.pt"
            config = DeepSeaEnhancerConfig(config_path=config_path, checkpoint_path=checkpoint_path)
        self.config = config

        self._model: Optional[MultiTaskUNet] = None
        self._device: Optional[torch.device] = None
        self._restoration_targets: List[str] = []
        self._regression_targets: List[str] = []
        self._num_seg_classes: int = 0
        self._palette: Optional[np.ndarray] = None

        if auto_prepare:
            self.ensure_ready()

    # ------------------------------------------------------------------
    # Discovery helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _discover_root(root_hint: Optional[Path]) -> Path:
        if root_hint is not None:
            root_hint = Path(root_hint).expanduser().resolve()
            if root_hint.exists():
                return root_hint
        env = os.getenv("KOSMOS_DEEPSEA_ROOT")
        if env:
            env_path = Path(env).expanduser()
            if env_path.exists():
                return env_path
        # Walk parents to locate a sibling DeepSeaEnhance folder.
        start = Path(__file__).resolve()
        for parent in start.parents:
            candidate = parent / "DeepSeaEnhance"
            if candidate.exists():
                return candidate
            nested = parent / "Sohaib(Personal)" / "DeepSeaEnhance"
            if nested.exists():
                return nested
        raise FileNotFoundError(
            "Unable to locate DeepSeaEnhance assets. Provide a valid path via "
            "`root_hint` or the `KOSMOS_DEEPSEA_ROOT` environment variable."
        )

    # ------------------------------------------------------------------
    # Preparation / inference
    # ------------------------------------------------------------------
    def ensure_ready(self) -> None:
        if self._model is not None:
            return
        cfg_path = self.config.config_path
        chk_path = self.config.checkpoint_path
        if not cfg_path.exists():
            raise FileNotFoundError(f"DeepSeaEnhance config introuvable: {cfg_path}")
        if not chk_path.exists():
            raise FileNotFoundError(f"DeepSeaEnhance checkpoint introuvable: {chk_path}")

        with open(cfg_path, "r", encoding="utf-8") as handle:
            cfg = yaml.safe_load(handle)

        data_cfg = cfg.get("data", {})
        model_cfg = cfg.get("model", {})

        self._restoration_targets = list(data_cfg.get("restoration_targets") or [])
        self._regression_targets = list(data_cfg.get("regression_targets") or [])
        self._num_seg_classes = int(model_cfg.get("num_classes", 0) or 0)

        restoration_channels = 3 * len(self._restoration_targets)
        regression_channels = len(self._regression_targets)

        device_str = self.config.device_override
        if device_str:
            self._device = torch.device(device_str)
        else:
            if torch.cuda.is_available():
                self._device = torch.device("cuda")
            elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():  # type: ignore[attr-defined]
                self._device = torch.device("mps")
            else:
                self._device = torch.device("cpu")

        self._model = MultiTaskUNet(
            in_channels=model_cfg.get("in_channels", 3),
            num_classes=self._num_seg_classes,
            regression_channels=regression_channels,
            restoration_channels=restoration_channels,
            encoder_name=model_cfg.get("encoder", "resnet34"),
            encoder_pretrained=model_cfg.get("encoder_pretrained", True),
            decoder_base_channels=model_cfg.get("decoder_base_channels", 256),
        ).to(self._device)

        checkpoint = torch.load(chk_path, map_location=self._device)
        state = checkpoint.get("model_state", checkpoint)
        self._model.load_state_dict(state)
        self._model.eval()

    def enhance(self, frame_bgr: np.ndarray) -> DeepSeaEnhancerResult:
        """
        Run the enhancer on a single BGR frame and return the processed outputs.
        """
        self.ensure_ready()
        assert self._model is not None and self._device is not None
        if frame_bgr.dtype != np.uint8:
            raise ValueError("The enhancer expects uint8 BGR frames in range [0, 255].")

        start = time.perf_counter()
        tensor = _to_tensor(frame_bgr).unsqueeze(0).to(self._device)
        with torch.no_grad():
            outputs = self._model(tensor)
        latency_ms = (time.perf_counter() - start) * 1000.0

        result = DeepSeaEnhancerResult()
        result.meta["latency_ms"] = latency_ms
        result.meta["device"] = str(self._device)
        result.meta["restoration_targets"] = list(self._restoration_targets)
        result.meta["regression_targets"] = list(self._regression_targets)

        if "restoration" in outputs:
            restored = outputs["restoration"][0].cpu()
            chunks = (
                torch.chunk(restored, len(self._restoration_targets), dim=0)
                if self._restoration_targets
                else (restored,)
            )
            for chunk in chunks:
                rgb = (chunk.clamp(0, 1).permute(1, 2, 0).numpy() * 255.0).astype(np.uint8)
                result.restored_bgr.append(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))

        if "segmentation" in outputs and self._num_seg_classes > 0:
            probs = torch.softmax(outputs["segmentation"], dim=1)
            mask = torch.argmax(probs, dim=1)[0].cpu().numpy().astype(np.uint8)
            result.mask = mask
            palette = self._get_palette()
            color_mask = palette[mask]
            result.overlay_bgr = cv2.addWeighted(
                frame_bgr,
                0.6,
                cv2.cvtColor(color_mask, cv2.COLOR_RGB2BGR),
                0.4,
                0,
            )

        if "regression" in outputs:
            result.regression = outputs["regression"][0].cpu().numpy()

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_palette(self) -> np.ndarray:
        if self._palette is not None:
            return self._palette
        rng = np.random.default_rng(42)
        palette = rng.integers(0, 255, size=(max(1, self._num_seg_classes), 3), dtype=np.uint8)
        if self._num_seg_classes > 0:
            palette[0] = np.array([0, 0, 0], dtype=np.uint8)
        self._palette = palette
        return palette


def _to_tensor(frame_bgr: np.ndarray) -> torch.Tensor:
    """
    Convert a ``uint8`` OpenCV frame (BGR) to a PyTorch tensor in [0, 1].
    """
    if frame_bgr.dtype != np.uint8:
        raise ValueError("Expected uint8 input.")
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    return torch.from_numpy(np.transpose(rgb, (2, 0, 1)))
