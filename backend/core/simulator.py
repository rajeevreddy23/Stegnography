"""
Optimal Embedding Simulator for Spatial Steganography.
Implements the Ternary Gibbs-Boltzmann optimal embedding simulator
with binary search / bisection for rate-distortion optimization:
P(y = x + 1) = exp(-lambda * rho+) / Z
P(y = x - 1) = exp(-lambda * rho-) / Z
P(y = x)     = 1 / Z
where Z = 1 + exp(-lambda * rho+) + exp(-lambda * rho-)
Entropy H(P) matches the target payload in bits.
Used for academic experiments and theoretical bound comparisons.
"""

import numpy as np
from typing import Tuple, Dict, Any, Optional
from .costs import get_initial_costs, WET_COST
from .cmd_stego import (
    compute_texture_complexity,
    get_subimage_indices,
    count_directional_neighbors_4,
    count_directional_neighbors_8_weighted,
)


def ternary_entropy(p_minus: np.ndarray, p_zero: np.ndarray, p_plus: np.ndarray) -> float:
    """Computes the total ternary Shannon entropy in bits."""
    h = 0.0
    for p in (p_minus, p_zero, p_plus):
        valid = p > 1e-15
        h -= np.sum(p[valid] * np.log2(p[valid]))
    return float(h)


def find_lambda_bisection(
    rho_plus: np.ndarray,
    rho_minus: np.ndarray,
    target_bits: float,
    max_iters: int = 50,
    tol: float = 1e-3,
) -> Tuple[float, np.ndarray, np.ndarray, np.ndarray]:
    """
    Finds the Gibbs-Boltzmann scaling factor lambda using binary search (bisection)
    such that total ternary entropy equals target_bits.
    """
    n = len(rho_plus)
    max_entropy = n * np.log2(3.0)
    if target_bits >= max_entropy:
        target_bits = max_entropy * 0.999

    # Bisection search bounds for lambda
    l_min = 1e-8
    l_max = 1e3

    # Ensure l_max gives entropy < target_bits
    for _ in range(10):
        em_p = np.exp(-np.clip(l_max * rho_plus, 0, 700))
        em_m = np.exp(-np.clip(l_max * rho_minus, 0, 700))
        z = 1.0 + em_p + em_m
        h_val = ternary_entropy(em_m / z, 1.0 / z, em_p / z)
        if h_val < target_bits:
            break
        l_max *= 10.0

    p_p = np.zeros(n)
    p_m = np.zeros(n)
    p_0 = np.zeros(n)

    for _ in range(max_iters):
        l_mid = (l_min + l_max) / 2.0
        em_p = np.exp(-np.clip(l_mid * rho_plus, 0, 700))
        em_m = np.exp(-np.clip(l_mid * rho_minus, 0, 700))
        z = 1.0 + em_p + em_m

        p_p = em_p / z
        p_m = em_m / z
        p_0 = 1.0 / z

        h_mid = ternary_entropy(p_m, p_0, p_p)

        if abs(h_mid - target_bits) < tol or (l_max - l_min) < 1e-9:
            break

        if h_mid > target_bits:
            l_min = l_mid
        else:
            l_max = l_mid

    return l_mid, p_m, p_0, p_p


def simulate_embedding(
    cover: np.ndarray,
    payload_bpp: float,
    scheme: str = "HILL",
    cmd_enabled: bool = True,
    L: int = 2,
    alpha: float = 9.0,
    adaptive_alpha: bool = False,
    neighborhood_8: bool = False,
    key_randomized: bool = False,
    seed: int = 42,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Simulates optimal steganographic embedding using Gibbs-Boltzmann distribution.
    Supports baseline additive embedding or iterative CMD clustering.
    """
    cover = cover.astype(np.uint8)
    H, W = cover.shape
    total_pixels = H * W
    target_total_bits = payload_bpp * total_pixels

    rng = np.random.RandomState(seed)

    if not cmd_enabled:
        # Standard additive baseline (HILL, S-UNIWARD, WOW without CMD)
        rho_p, rho_m = get_initial_costs(cover, scheme=scheme)
        l_val, p_m, p_0, p_p = find_lambda_bisection(rho_p.ravel(), rho_m.ravel(), target_total_bits)

        # Draw ternary modifications
        u = rng.uniform(0.0, 1.0, size=total_pixels)
        mod = np.zeros(total_pixels, dtype=np.int16)
        mod[u < p_m] = -1
        mod[(u >= p_m) & (u < (p_m + p_p))] = 1

        stego = np.clip(cover.astype(np.int16) + mod.reshape((H, W)), 0, 255).astype(np.uint8)
        diff = stego.astype(np.int16) - cover.astype(np.int16)
        changes = np.sum(diff != 0)

        return stego, {
            'scheme': scheme,
            'cmd_enabled': False,
            'bpp': payload_bpp,
            'total_bits': target_total_bits,
            'changes': int(changes),
            'change_rate': float(changes) / total_pixels,
            'pos_changes': int(np.sum(diff == 1)),
            'neg_changes': int(np.sum(diff == -1)),
        }

    # CMD-enabled simulation
    subimages = get_subimage_indices(
        height=H,
        width=W,
        L=L,
        stego_key=str(seed),
        key_randomized=key_randomized,
        exclude_header=False,
    )
    num_sub = len(subimages)
    sub_target_bits = target_total_bits / float(num_sub)

    if adaptive_alpha:
        tex_map = compute_texture_complexity(cover)
        alpha_min = max(2.0, alpha * 0.4)
        alpha_max = alpha * 1.8
        alpha_map = alpha_min + (alpha_max - alpha_min) * tex_map
    else:
        alpha_map = np.full((H, W), fill_value=alpha, dtype=np.float64)

    Y = cover.copy()

    for t in range(num_sub):
        coords = subimages[t]
        r_idx = coords[:, 0]
        c_idx = coords[:, 1]
        cover_sub = Y[r_idx, c_idx]
        sub_n = len(coords)

        if t == 0:
            rho_plus_full, rho_minus_full = get_initial_costs(cover, scheme=scheme)
            sub_rho_p = rho_plus_full[r_idx, c_idx].copy()
            sub_rho_m = rho_minus_full[r_idx, c_idx].copy()
        else:
            D = Y.astype(np.int16) - cover.astype(np.int16)
            base_rho_p, base_rho_m = get_initial_costs(Y, scheme=scheme)
            sub_rho_p = base_rho_p[r_idx, c_idx].copy()
            sub_rho_m = base_rho_m[r_idx, c_idx].copy()

            for k in range(sub_n):
                r, c = coords[k]
                local_alpha = alpha_map[r, c]
                base_c = sub_rho_p[k]

                if neighborhood_8:
                    score = count_directional_neighbors_8_weighted(D, r, c, H, W)
                    if score > 0.25:
                        sub_rho_p[k] = base_c / local_alpha
                        sub_rho_m[k] = base_c
                    elif score < -0.25:
                        sub_rho_m[k] = base_c / local_alpha
                        sub_rho_p[k] = base_c
                    else:
                        sub_rho_p[k] = base_c
                        sub_rho_m[k] = base_c
                else:
                    pos_c, neg_c = count_directional_neighbors_4(D, r, c, H, W)
                    if pos_c > neg_c:
                        sub_rho_p[k] = base_c / local_alpha
                        sub_rho_m[k] = base_c
                    elif neg_c > pos_c:
                        sub_rho_m[k] = base_c / local_alpha
                        sub_rho_p[k] = base_c
                    else:
                        sub_rho_p[k] = base_c
                        sub_rho_m[k] = base_c

        sub_rho_m[cover_sub == 0] = WET_COST
        sub_rho_p[cover_sub == 255] = WET_COST

        l_val, p_m, p_0, p_p = find_lambda_bisection(sub_rho_p, sub_rho_m, sub_target_bits)

        u = rng.uniform(0.0, 1.0, size=sub_n)
        sub_mod = np.zeros(sub_n, dtype=np.int16)
        sub_mod[u < p_m] = -1
        sub_mod[(u >= p_m) & (u < (p_m + p_p))] = 1

        new_vals = np.clip(cover_sub.astype(np.int16) + sub_mod, 0, 255).astype(np.uint8)
        Y[r_idx, c_idx] = new_vals

    diff = Y.astype(np.int16) - cover.astype(np.int16)
    changes = np.sum(diff != 0)

    return Y, {
        'scheme': scheme,
        'cmd_enabled': True,
        'bpp': payload_bpp,
        'total_bits': target_total_bits,
        'changes': int(changes),
        'change_rate': float(changes) / total_pixels,
        'pos_changes': int(np.sum(diff == 1)),
        'neg_changes': int(np.sum(diff == -1)),
        'L': L,
        'alpha': alpha,
        'adaptive_alpha': adaptive_alpha,
        'neighborhood_8': neighborhood_8,
    }
