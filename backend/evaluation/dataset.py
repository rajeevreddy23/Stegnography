"""
Dataset Management for CMD-Stego+ Benchmark & Evaluation.
Supports:
- Loading BOSSBase 1.01 grayscale images if available in data/
- Automatic generation of realistic synthetic natural/texture 512x512 grayscale images
  with authentic spatial gradients, multi-scale textures, and edges
- Configuration for fast runs (50-500 images) and full-scale runs (10,000 images)
"""

import os
import glob
import cv2
import numpy as np
from typing import List, Optional


def generate_synthetic_cover(index: int, size: int = 512) -> np.ndarray:
    """
    Generates a realistic 512x512 grayscale image possessing natural spatial correlations,
    multi-scale texture variations, smooth gradients, and sharp edge boundaries.
    """
    rng = np.random.RandomState(index * 1337 + 42)
    img = np.zeros((size, size), dtype=np.float64)

    # 1. Base low-frequency illumination gradient
    gx = np.linspace(rng.uniform(0.1, 0.9), rng.uniform(0.1, 0.9), size)
    gy = np.linspace(rng.uniform(0.1, 0.9), rng.uniform(0.1, 0.9), size)
    GX, GY = np.meshgrid(gx, gy)
    angle = rng.uniform(0, 2 * np.pi)
    base_grad = np.cos(angle) * GX + np.sin(angle) * GY
    img += base_grad * rng.uniform(40, 90) + rng.uniform(80, 160)

    # 2. Multi-scale Perlin-like fractal octave noise for natural textures
    for scale, weight in [(64, 30.0), (32, 18.0), (16, 10.0), (8, 5.0)]:
        grid_h = size // scale + 1
        grid_w = size // scale + 1
        low_res = rng.randn(grid_h, grid_w)
        high_res = cv2.resize(low_res, (size, size), interpolation=cv2.INTER_CUBIC)
        img += high_res * weight

    # 3. Geometric edges / structures (simulating objects, buildings, natural scenes)
    num_shapes = rng.randint(3, 8)
    for _ in range(num_shapes):
        shape_type = rng.choice(['line', 'circle', 'poly'])
        contrast = rng.uniform(-35, 35)
        if shape_type == 'circle':
            center = (rng.randint(50, size - 50), rng.randint(50, size - 50))
            radius = rng.randint(20, 120)
            Y, X = np.ogrid[:size, :size]
            dist_sq = (X - center[0]) ** 2 + (Y - center[1]) ** 2
            mask = dist_sq <= radius ** 2
            img[mask] += contrast
        elif shape_type == 'line':
            pt1 = (rng.randint(0, size), rng.randint(0, size))
            pt2 = (rng.randint(0, size), rng.randint(0, size))
            line_mask = np.zeros((size, size), dtype=np.uint8)
            cv2.line(line_mask, pt1, pt2, 1, thickness=rng.randint(2, 6))
            img[line_mask == 1] += contrast

    # 4. Blur edges slightly for natural MTF optical response
    img = cv2.GaussianBlur(img, (3, 3), 0.8)

    # Clip to valid 8-bit range [0, 255]
    cover = np.clip(np.round(img), 0, 255).astype(np.uint8)
    return cover


def prepare_dataset(
    data_dir: str = "d:/Stegnography/data/covers",
    num_images: int = 50,
    size: int = 512,
) -> List[str]:
    """
    Scans data_dir for existing grayscale images.
    If fewer than num_images exist, generates the remainder and saves them as PNG.
    Returns list of file paths.
    """
    os.makedirs(data_dir, exist_ok=True)

    # Find existing images
    patterns = [os.path.join(data_dir, "*.png"), os.path.join(data_dir, "*.pgm"), os.path.join(data_dir, "*.jpg")]
    existing_files = []
    for p in patterns:
        existing_files.extend(glob.glob(p))

    existing_files.sort()
    if len(existing_files) >= num_images:
        return existing_files[:num_images]

    # Generate needed images
    needed = num_images - len(existing_files)
    current_count = len(existing_files)
    print(f"Dataset: found {current_count} covers, generating {needed} synthetic covers in {data_dir}...")

    generated_paths = []
    for i in range(needed):
        idx = current_count + i + 1
        img = generate_synthetic_cover(index=idx, size=size)
        file_path = os.path.join(data_dir, f"cover_{idx:05d}.png")
        cv2.imwrite(file_path, img)
        generated_paths.append(file_path)

    all_paths = existing_files + generated_paths
    all_paths.sort()
    return all_paths[:num_images]


def load_grayscale_image(path: str, size: Optional[int] = 512) -> np.ndarray:
    """Loads an image from disk and converts to 8-bit grayscale, optionally resizing."""
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Failed to read image at: {path}")
    if size is not None and (img.shape[0] != size or img.shape[1] != size):
        img = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
    return img
