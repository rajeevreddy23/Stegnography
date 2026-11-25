"""
PyTorch Steganalyzer: SRNet-lite.
A lightweight, CPU-efficient deep learning steganalyzer inspired by SRNet
(Boroumand, Chen, Fridrich, IEEE TIFS 2018).
Designed for real-time live scoring and rapid training on spatial stego pairs.
"""

import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from typing import Tuple, Dict, Any, Optional, List


class ResidualBlock(nn.Module):
    def __init__(self, channels: int):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
        )
        self.relu = nn.LeakyReLU(0.2, inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.relu(x + self.conv(x))


class SRNetLite(nn.Module):
    def __init__(self):
        super().__init__()
        # Layer 1: Residual extraction (no pooling to preserve high-frequency stego noise)
        self.layer1 = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(16),
            nn.LeakyReLU(0.2, inplace=True),
        )
        # Layer 2: Feature consolidation
        self.layer2 = nn.Sequential(
            nn.Conv2d(16, 32, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.LeakyReLU(0.2, inplace=True),
        )
        # Layer 3: Deep residual abstraction
        self.res1 = ResidualBlock(32)
        # Layer 4: Pooling and downsampling
        self.layer4 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.LeakyReLU(0.2, inplace=True),
        )
        self.res2 = ResidualBlock(64)
        # Global Average Pooling
        self.gap = nn.AdaptiveAvgPool2d((1, 1))
        # Final classification head: 2 classes (0: Cover, 1: Stego)
        self.fc = nn.Linear(64, 2)

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='leaky_relu')
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1.0)
                nn.init.constant_(m.bias, 0.0)
            elif isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                nn.init.constant_(m.bias, 0.0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.layer1(x)
        out = self.layer2(out)
        out = self.res1(out)
        out = self.layer4(out)
        out = self.res2(out)
        out = self.gap(out)
        out = torch.flatten(out, 1)
        logits = self.fc(out)
        return logits


class StegoDataset(Dataset):
    def __init__(self, images: List[np.ndarray], labels: List[int]):
        self.images = images
        self.labels = labels

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx: int):
        img = self.images[idx].astype(np.float32) / 255.0
        # If larger than 256x256, take center crop for fast uniform training
        H, W = img.shape
        if H > 256 or W > 256:
            r0 = (H - 256) // 2
            c0 = (W - 256) // 2
            img = img[r0:r0+256, c0:c0+256]
        tensor_img = torch.from_numpy(img).unsqueeze(0)  # [1, H, W]
        label = torch.tensor(self.labels[idx], dtype=torch.long)
        return tensor_img, label


def train_srnet(
    covers: List[np.ndarray],
    stegos: List[np.ndarray],
    epochs: int = 15,
    batch_size: int = 16,
    lr: float = 1e-3,
    save_path: Optional[str] = None,
    device_str: str = "cpu",
) -> Tuple[SRNetLite, Dict[str, Any]]:
    """
    Trains SRNet-lite model on pairs of Cover and Stego images.
    Returns (trained_model, history_dict).
    """
    device = torch.device(device_str)
    model = SRNetLite().to(device)

    # Prepare dataset
    all_images = covers + stegos
    all_labels = [0] * len(covers) + [1] * len(stegos)

    # 80/20 train/val split
    indices = np.random.permutation(len(all_images))
    split_idx = int(0.8 * len(all_images))
    train_idx = indices[:split_idx]
    val_idx = indices[split_idx:]

    train_ds = StegoDataset([all_images[i] for i in train_idx], [all_labels[i] for i in train_idx])
    val_ds = StegoDataset([all_images[i] for i in val_idx], [all_labels[i] for i in val_idx])

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    history = {'train_loss': [], 'val_pe': [], 'val_accuracy': []}

    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        for x_b, y_b in train_loader:
            x_b, y_b = x_b.to(device), y_b.to(device)
            optimizer.zero_grad()
            logits = model(x_b)
            loss = criterion(logits, y_b)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(y_b)

        epoch_loss = total_loss / len(train_ds)
        history['train_loss'].append(epoch_loss)

        # Validation evaluation
        eval_metrics = evaluate_srnet(model, val_loader, device)
        history['val_pe'].append(eval_metrics['p_e'])
        history['val_accuracy'].append(eval_metrics['accuracy'])

    if save_path:
        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        torch.save(model.state_dict(), save_path)

    return model, history


def evaluate_srnet(model: SRNetLite, data_loader: DataLoader, device: torch.device) -> Dict[str, float]:
    """Evaluates SRNet-lite, returning P_E = (FPR + FNR) / 2 and accuracy."""
    model.eval()
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for x_b, y_b in data_loader:
            x_b = x_b.to(device)
            logits = model(x_b)
            preds = torch.argmax(logits, dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_targets.extend(y_b.numpy())

    preds = np.array(all_preds)
    targets = np.array(all_targets)

    cover_mask = (targets == 0)
    stego_mask = (targets == 1)

    fpr = float(np.mean(preds[cover_mask] == 1)) if np.any(cover_mask) else 0.0
    fnr = float(np.mean(preds[stego_mask] == 0)) if np.any(stego_mask) else 0.0
    p_e = (fpr + fnr) / 2.0
    acc = float(np.mean(preds == targets))

    return {
        'p_e': round(p_e, 4),
        'fpr': round(fpr, 4),
        'fnr': round(fnr, 4),
        'accuracy': round(acc, 4),
    }


def predict_stego_probability(model: SRNetLite, image: np.ndarray, device_str: str = "cpu") -> float:
    """Predicts the probability that an image is Stego [0.0 = Cover, 1.0 = Stego]."""
    device = torch.device(device_str)
    model.eval()
    img = image.astype(np.float32) / 255.0
    H, W = img.shape
    if H > 256 or W > 256:
        r0 = (H - 256) // 2
        c0 = (W - 256) // 2
        img = img[r0:r0+256, c0:c0+256]

    tensor_img = torch.from_numpy(img).unsqueeze(0).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(tensor_img)
        probs = torch.softmax(logits, dim=1).cpu().numpy()
        stego_prob = float(probs[0, 1])
    return round(stego_prob, 4)
