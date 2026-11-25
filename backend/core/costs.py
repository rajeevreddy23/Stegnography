"""
Distortion Cost Functions for Spatial Steganography.
Implements:
1. HILL (High-pass, Low-pass, Low-pass) - Li et al., 2014
2. S-UNIWARD (Spatial Universal Wavelet Relative Distortion) - Holub et al., 2014
3. WOW (Wavelet Optimized Weighted) - Holub & Fridrich, 2012
With mirror reflection padding and wet cost assignment (1e10) for boundary saturation.
"""

import cv2
import numpy as np
from typing import Tuple

WET_COST = 1e10


def compute_hill_costs(cover: np.ndarray) -> np.ndarray:
    """
    Computes initial additive distortion costs using the HILL algorithm:
    C = 1 / (|X (x) H| (x) P1) (x) P2
    Where:
    - H: 3x3 KB high-pass filter: [[-1, 2, -1], [2, -4, 2], [-1, 2, -1]]
    - P1: 3x3 low-pass averaging filter (1/9)
    - P2: 15x15 low-pass averaging filter (1/225)
    - Mirror padding (BORDER_REFLECT) applied at each convolution stage.
    """
    img = cover.astype(np.float64)

    # 3x3 KB high-pass filter
    H = np.array([
        [-1.0,  2.0, -1.0],
        [ 2.0, -4.0,  2.0],
        [-1.0,  2.0, -1.0]
    ], dtype=np.float64)

    # Low-pass smoothing filters
    P1 = np.ones((3, 3), dtype=np.float64) / 9.0
    P2 = np.ones((15, 15), dtype=np.float64) / 225.0

    # Step 1: High-pass residual R = |X (x) H| with mirror padding
    residual = np.abs(cv2.filter2D(img, -1, H, borderType=cv2.BORDER_REFLECT))

    # Step 2: Smoothing with P1 and reciprocal
    smoothed_r = cv2.filter2D(residual, -1, P1, borderType=cv2.BORDER_REFLECT)
    W = 1.0 / (smoothed_r + 1e-10)

    # Step 3: Smoothing with P2
    C = cv2.filter2D(W, -1, P2, borderType=cv2.BORDER_REFLECT)

    # Normalize to avoid extreme numerical issues while preserving relative ratios
    C[np.isnan(C) | np.isinf(C)] = 1e5
    return C


def compute_suniward_costs(cover: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    """
    Computes spatial S-UNIWARD distortion costs using 2D directional wavelet filter bank.
    Wavelet filters: LH, HL, HH derived from 1D low-pass and high-pass filters.
    """
    img = cover.astype(np.float64)
    # 1D filters
    h = np.array([1.0, 2.0, 1.0], dtype=np.float64) / 4.0
    g = np.array([1.0, -2.0, 1.0], dtype=np.float64) / 4.0

    F_LH = np.outer(h, g)
    F_HL = np.outer(g, h)
    F_HH = np.outer(g, g)

    P = np.ones((15, 15), dtype=np.float64) / 225.0

    C = np.zeros_like(img)
    for F in (F_LH, F_HL, F_HH):
        res = np.abs(cv2.filter2D(img, -1, F, borderType=cv2.BORDER_REFLECT))
        w = 1.0 / (res + sigma)
        smoothed = cv2.filter2D(w, -1, P, borderType=cv2.BORDER_REFLECT)
        C += smoothed

    C /= 3.0
    return C


def compute_wow_costs(cover: np.ndarray) -> np.ndarray:
    """
    Computes spatial WOW (Wavelet Optimized Weighted) distortion costs.
    """
    img = cover.astype(np.float64)
    # Directional Daubechies-like filter approximations
    F1 = np.array([[-1.0, 2.0, -1.0], [2.0, -4.0, 2.0], [-1.0, 2.0, -1.0]], dtype=np.float64)
    F2 = np.array([[1.0, -2.0, 1.0], [-2.0, 4.0, -2.0], [1.0, -2.0, 1.0]], dtype=np.float64)

    P1 = np.ones((3, 3), dtype=np.float64) / 9.0
    P2 = np.ones((11, 11), dtype=np.float64) / 121.0

    r1 = np.abs(cv2.filter2D(img, -1, F1, borderType=cv2.BORDER_REFLECT))
    r2 = np.abs(cv2.filter2D(img, -1, F2, borderType=cv2.BORDER_REFLECT))

    s1 = cv2.filter2D(r1, -1, P1, borderType=cv2.BORDER_REFLECT)
    s2 = cv2.filter2D(r2, -1, P1, borderType=cv2.BORDER_REFLECT)

    w = 1.0 / (s1 + s2 + 1e-10)
    C = cv2.filter2D(w, -1, P2, borderType=cv2.BORDER_REFLECT)
    return C


def get_initial_costs(cover: np.ndarray, scheme: str = "HILL") -> Tuple[np.ndarray, np.ndarray]:
    """
    Computes the initial (rho+, rho-) cost maps for a given cover image and baseline scheme.
    Applies wet cost (1e10) to saturated pixels:
    - If cover[i,j] == 0: rho-[i,j] = WET_COST (cannot modify by -1)
    - If cover[i,j] == 255: rho+[i,j] = WET_COST (cannot modify by +1)
    """
    scheme_upper = scheme.upper()
    if "UNIWARD" in scheme_upper:
        C = compute_suniward_costs(cover)
    elif "WOW" in scheme_upper:
        C = compute_wow_costs(cover)
    else:  # Default HILL
        C = compute_hill_costs(cover)

    rho_plus = C.copy()
    rho_minus = C.copy()

    # Wet cost boundary handling
    rho_minus[cover == 0] = WET_COST
    rho_plus[cover == 255] = WET_COST

    return rho_plus, rho_minus
