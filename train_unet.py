"""
Training script for U-Net fish segmentation.
Assumes dataset folders:
  {data_root}/train/images/*.png|jpg
  {data_root}/train/masks/*.png|jpg  (binary masks, 0 background, 1 fish)
  {data_root}/val/images, {data_root}/val/masks
Update --data-root if your data lives elsewhere.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Dict, List, Tuple

import albumentations as A
import cv2
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm


def list_pairs(root: Path, split: str) -> Tuple[List[Path], List[Path]]:
    images = sorted((root / split / "images").glob("*"))
    masks = sorted((root / split / "masks").glob("*"))
    if not images or not masks:
        raise FileNotFoundError(f"No data found in {root}/{split}/images or masks")
    if len(images) != len(masks):
        raise ValueError(f"Images ({len(images)}) and masks ({len(masks)}) count mismatch in {split}")
    return images, masks


class FishDataset(Dataset):
    def __init__(
        self,
        root: Path,
        split: str,
        size: int = 512,
        augment: bool = False,
        normalize: Dict[str, List[float]] | None = None,
    ):
        self.images, self.masks = list_pairs(root, split)
        self.size = size
        norm = []
        if normalize:
            norm = [A.Normalize(mean=normalize["mean"], std=normalize["std"])]
        if augment:
            self.transform = A.Compose(
                [
                    A.HorizontalFlip(p=0.5),
                    A.VerticalFlip(p=0.1),
                    A.RandomRotate90(p=0.25),
                    A.ColorJitter(p=0.3),
                    A.GaussianBlur(p=0.1),
                    A.ShiftScaleRotate(shift_limit=0.05, scale_limit=0.1, rotate_limit=10, p=0.25),
                    A.Resize(size, size),
                ]
                + norm
            )
        else:
            self.transform = A.Compose(
                [
                    A.Resize(size, size),
                ]
            )

    def __len__(self) -> int:
        return len(self.images)

    def __getitem__(self, idx: int):
        image = cv2.cvtColor(cv2.imread(str(self.images[idx])), cv2.COLOR_BGR2RGB)
        mask = cv2.imread(str(self.masks[idx]), cv2.IMREAD_GRAYSCALE)
        if mask is None or image is None:
            raise ValueError(f"Failed to read pair: {self.images[idx]} / {self.masks[idx]}")
        transformed = self.transform(image=image, mask=mask)
        image = transformed["image"]
        mask = transformed["mask"]
        image = torch.from_numpy(image).float().permute(2, 0, 1) / 255.0
        mask = torch.from_numpy((mask > 0).astype(np.float32)).unsqueeze(0)
        return image, mask


class DoubleConv(nn.Module):
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class UNet(nn.Module):
    def __init__(self, base: int = 32):
        super().__init__()
        self.down1 = DoubleConv(3, base)
        self.down2 = DoubleConv(base, base * 2)
        self.down3 = DoubleConv(base * 2, base * 4)
        self.down4 = DoubleConv(base * 4, base * 8)
        self.bottom = DoubleConv(base * 8, base * 16)
        self.pool = nn.MaxPool2d(2)

        self.up4 = nn.ConvTranspose2d(base * 16, base * 8, kernel_size=2, stride=2)
        self.conv_up4 = DoubleConv(base * 16, base * 8)
        self.up3 = nn.ConvTranspose2d(base * 8, base * 4, kernel_size=2, stride=2)
        self.conv_up3 = DoubleConv(base * 8, base * 4)
        self.up2 = nn.ConvTranspose2d(base * 4, base * 2, kernel_size=2, stride=2)
        self.conv_up2 = DoubleConv(base * 4, base * 2)
        self.up1 = nn.ConvTranspose2d(base * 2, base, kernel_size=2, stride=2)
        self.conv_up1 = DoubleConv(base * 2, base)

        self.out = nn.Conv2d(base, 1, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        c1 = self.down1(x)
        p1 = self.pool(c1)
        c2 = self.down2(p1)
        p2 = self.pool(c2)
        c3 = self.down3(p2)
        p3 = self.pool(c3)
        c4 = self.down4(p3)
        p4 = self.pool(c4)

        b = self.bottom(p4)

        u4 = self.up4(b)
        u4 = torch.cat([u4, c4], dim=1)
        u4 = self.conv_up4(u4)

        u3 = self.up3(u4)
        u3 = torch.cat([u3, c3], dim=1)
        u3 = self.conv_up3(u3)

        u2 = self.up2(u3)
        u2 = torch.cat([u2, c2], dim=1)
        u2 = self.conv_up2(u2)

        u1 = self.up1(u2)
        u1 = torch.cat([u1, c1], dim=1)
        u1 = self.conv_up1(u1)

        return self.out(u1)


def build_model(model_name: str, base: int, encoder: str, encoder_weights: str | None) -> nn.Module:
    if model_name == "smp":
        import segmentation_models_pytorch as smp

        return smp.Unet(
            encoder_name=encoder,
            encoder_weights=encoder_weights,
            in_channels=3,
            classes=1,
        )
    return UNet(base=base)


def dice_loss(pred: torch.Tensor, target: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    pred = torch.sigmoid(pred)
    num = 2 * (pred * target).sum(dim=[1, 2, 3])
    den = pred.sum(dim=[1, 2, 3]) + target.sum(dim=[1, 2, 3]) + eps
    return 1 - (num / den).mean()


def iou_score(logits: torch.Tensor, mask: torch.Tensor, thr: float = 0.5, eps: float = 1e-6) -> float:
    pred = (torch.sigmoid(logits) > thr).float()
    inter = (pred * mask).sum(dim=[1, 2, 3])
    union = pred.sum(dim=[1, 2, 3]) + mask.sum(dim=[1, 2, 3]) - inter
    return ((inter + eps) / (union + eps)).mean().item()


def train(
    data_root: Path,
    epochs: int,
    batch_size: int,
    lr: float,
    size: int,
    device: str,
    model_name: str,
    base_channels: int,
    encoder: str,
    encoder_weights: str | None,
    use_amp: bool,
) -> None:
    normalize = None
    if model_name == "smp" and encoder_weights:
        normalize = {"mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]}

    train_ds = FishDataset(data_root, "train", size=size, augment=True, normalize=normalize)
    val_ds = FishDataset(data_root, "val", size=size, augment=False, normalize=normalize)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=2, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=2, pin_memory=True)

    model = build_model(model_name=model_name, base=base_channels, encoder=encoder, encoder_weights=encoder_weights).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=3, verbose=True)
    bce = nn.BCEWithLogitsLoss()
    best_iou = 0.0
    artifacts = Path("artifacts")
    artifacts.mkdir(exist_ok=True)
    scaler = torch.cuda.amp.GradScaler(enabled=use_amp)

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        for imgs, masks in tqdm(train_loader, desc=f"Epoch {epoch}/{epochs}", leave=False):
            imgs, masks = imgs.to(device), masks.to(device)
            with torch.cuda.amp.autocast(enabled=use_amp):
                logits = model(imgs)
                loss = bce(logits, masks) + dice_loss(logits, masks)
            optimizer.zero_grad()
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            running_loss += loss.item() * imgs.size(0)

        model.eval()
        val_ious: List[float] = []
        with torch.no_grad():
            for imgs, masks in val_loader:
                imgs, masks = imgs.to(device), masks.to(device)
                logits = model(imgs)
                val_ious.append(iou_score(logits, masks))

        epoch_loss = running_loss / len(train_ds)
        mean_iou = float(np.mean(val_ious))
        print(f"Epoch {epoch}: loss={epoch_loss:.4f} val_iou={mean_iou:.4f}")
        scheduler.step(mean_iou)

        if mean_iou > best_iou:
            best_iou = mean_iou
            torch.save(
                {
                    "model_state": model.state_dict(),
                    "best_iou": best_iou,
                    "size": size,
                    "model_name": model_name,
                    "encoder": encoder,
                    "encoder_weights": encoder_weights,
                },
                artifacts / "best_unet_fish.pth",
            )
            print(f"Saved new best model with IoU={best_iou:.4f}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train U-Net for fish segmentation")
    parser.add_argument(
        "--data-root",
        type=str,
        default="/mnt/c/Users/USER/Downloads/Data_Kosmos",
        help="Path to dataset containing train/ and val/ folders",
    )
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--size", type=int, default=512, help="Resize images to size x size")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--model", type=str, choices=["simple", "smp"], default="smp", help="simple = custom UNet; smp = Unet from segmentation_models_pytorch")
    parser.add_argument("--base-channels", type=int, default=32, help="Base channels for simple UNet")
    parser.add_argument("--encoder", type=str, default="resnet34", help="Encoder backbone name when using smp")
    parser.add_argument(
        "--no-pretrained",
        action="store_true",
        help="Disable ImageNet pretrained encoder weights when using smp",
    )
    parser.add_argument("--amp", action="store_true", help="Use mixed precision (recommended on GPU)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_root = Path(args.data_root)
    if not data_root.exists():
        raise FileNotFoundError(f"Data root '{data_root}' not found")
    print(f"Using data root: {data_root}")
    encoder_weights = None
    if args.model == "smp" and not args.no_pretrained:
        encoder_weights = "imagenet"

    train(
        data_root=data_root,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        size=args.size,
        device=args.device,
        model_name=args.model,
        base_channels=args.base_channels,
        encoder=args.encoder,
        encoder_weights=encoder_weights,
        use_amp=args.amp,
    )


if __name__ == "__main__":
    main()
