"""
Evaluation Metrics for Spatial Steganography.
Implements:
- PSNR (Peak Signal-to-Noise Ratio)
- SSIM (Structural Similarity Index Measure)
- Change Rate & Directional Modification Counts
- FCC (Feature Continuity / Correlation: 2nd, 3rd, 4th order per IEEE TIFS 2015 paper)
"""

import numpy as np
from skimage.metrics import structural_similarity as ssim_fn
from typing import Dict, Any


def compute_psnr(cover: np.ndarray, stego: np.ndarray) -> float:
    """Computes Peak Signal-to-Noise Ratio in dB."""
    c = cover.astype(np.float64)
    s = stego.astype(np.float64)
    mse = np.mean((c - s) ** 2)
    if mse < 1e-12:
        return 100.0  # Identical images
    psnr = 10.0 * np.log10((255.0 ** 2) / mse)
    return float(psnr)


def compute_ssim(cover: np.ndarray, stego: np.ndarray) -> float:
    """Computes Structural Similarity Index (SSIM)."""
    return float(ssim_fn(cover, stego, data_range=255))


def compute_fcc(diff: np.ndarray) -> Dict[str, float]:
    """
    Computes Feature Continuity / Correlation (FCC) metrics of the modification direction matrix D.
    Based on Li et al. (IEEE TIFS 2015), Section II, Eq. (3)-(7).
    - FCC2: 2nd-order correlation between adjacent orthogonal modification directions.
    - FCC3: 3rd-order correlation across collinear triplet modification directions.
    - FCC4: 4th-order correlation across 2x2 square cliques.
    """
    D = diff.astype(np.float64)
    H, W = D.shape

    # 2nd-order FCC: Horizontal and Vertical neighbor pairs
    h_pairs = D[:, :-1] * D[:, 1:]
    v_pairs = D[:-1, :] * D[1:, :]
    num_pairs = h_pairs.size + v_pairs.size
    fcc2 = float(np.sum(h_pairs) + np.sum(v_pairs)) / float(num_pairs) if num_pairs > 0 else 0.0

    # 3rd-order FCC: Collinear horizontal and vertical triplets
    h_triplets = D[:, :-2] * D[:, 1:-1] * D[:, 2:]
    v_triplets = D[:-2, :] * D[1:-1, :] * D[2:, :]
    num_triplets = h_triplets.size + v_triplets.size
    fcc3 = float(np.sum(h_triplets) + np.sum(v_triplets)) / float(num_triplets) if num_triplets > 0 else 0.0

    # 4th-order FCC: 2x2 square cliques
    cliques = D[:-1, :-1] * D[1:, :-1] * D[:-1, 1:] * D[1:, 1:]
    num_cliques = cliques.size
    fcc4 = float(np.sum(cliques)) / float(num_cliques) if num_cliques > 0 else 0.0

    return {
        'fcc2': fcc2,
        'fcc3': fcc3,
        'fcc4': fcc4,
    }


def compute_all_metrics(cover: np.ndarray, stego: np.ndarray, embed_time_sec: float = 0.0) -> Dict[str, Any]:
    """
    Computes full set of evaluation metrics between cover and stego images.
    """
    cover = cover.astype(np.uint8)
    stego = stego.astype(np.uint8)
    diff = stego.astype(np.int16) - cover.astype(np.int16)

    H, W = cover.shape
    total_pixels = H * W
    changes = int(np.sum(diff != 0))
    pos_changes = int(np.sum(diff == 1))
    neg_changes = int(np.sum(diff == -1))
    change_rate = float(changes) / float(total_pixels)

    psnr_val = compute_psnr(cover, stego)
    ssim_val = compute_ssim(cover, stego)
    fcc_dict = compute_fcc(diff)

    return {
        'psnr': round(psnr_val, 3),
        'ssim': round(ssim_val, 5),
        'changes': changes,
        'pos_changes': pos_changes,
        'neg_changes': neg_changes,
        'change_rate': round(change_rate, 5),
        'fcc2': round(fcc_dict['fcc2'], 6),
        'fcc3': round(fcc_dict['fcc3'], 6),
        'fcc4': round(fcc_dict['fcc4'], 6),
        'embed_time_ms': round(embed_time_sec * 1000.0, 2),
    }
