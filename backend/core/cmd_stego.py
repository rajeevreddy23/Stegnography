"""
CMD-Stego+ Engine: Adaptive Clustering of Modification Directions.
Based on IEEE TIFS 2015 paper by Li, Wang, Li, Tan, Huang.
Implements:
- 64-bit autonomous header for robust payload length extraction
- L x L Interleaved sub-image decomposition (default L=2)
- Horizontal zig-zag and key-randomized embedding order
- Dynamic cost recomputation on stego Y
- 4-neighborhood voting & Novel 8-neighborhood weighted voting (Improvement C)
- Novel Adaptive-alpha texture complexity modulation (Improvement A)
- Key-based spatial lattice and pixel randomization (Improvement B)
- Cryptographic payload packaging & authentication (Improvement D)
"""

import hashlib
import cv2
import numpy as np
from typing import Tuple, List, Dict, Any, Optional

from .costs import get_initial_costs, WET_COST
from .stc import stc_embed, stc_extract
from .security import (
    pack_payload,
    unpack_payload,
    bytes_to_bits,
    bits_to_bytes,
)

HEADER_PIXELS = 64
HEADER_MAGIC = b'CMDS'


def encode_header(pixels: np.ndarray, total_bits: int) -> np.ndarray:
    """
    Encodes 64-bit header into the first 64 pixels using LSB parity:
    - 32-bit Magic 'CMDS'
    - 32-bit total_bits count
    """
    hdr_bytes = HEADER_MAGIC + int(total_bits).to_bytes(4, byteorder='big')
    hdr_bits = bytes_to_bits(hdr_bytes)

    out = pixels.copy()
    for i in range(min(HEADER_PIXELS, len(out))):
        target_bit = hdr_bits[i]
        curr_bit = out[i] % 2
        if curr_bit != target_bit:
            if out[i] == 0:
                out[i] = 1
            elif out[i] == 255:
                out[i] = 254
            else:
                out[i] = out[i] + 1
    return out


def decode_header(pixels: np.ndarray) -> Optional[int]:
    """
    Decodes the 64-bit header from the first 64 pixels.
    Returns total_bits if valid magic found, else None.
    """
    if len(pixels) < HEADER_PIXELS:
        return None
    hdr_bits = (pixels[:HEADER_PIXELS] % 2).astype(np.uint8)
    hdr_bytes = bits_to_bytes(hdr_bits)[:8]
    if hdr_bytes[:4] != HEADER_MAGIC:
        return None
    total_bits = int.from_bytes(hdr_bytes[4:8], byteorder='big')
    return total_bits


def compute_texture_complexity(cover: np.ndarray) -> np.ndarray:
    """
    Computes local texture complexity map via local 5x5 variance.
    Returns normalized texture map V_norm in [0.0, 1.0].
    """
    img = cover.astype(np.float64)
    kernel = np.ones((5, 5), dtype=np.float64) / 25.0

    mean = cv2.filter2D(img, -1, kernel, borderType=cv2.BORDER_REFLECT)
    sq_mean = cv2.filter2D(img * img, -1, kernel, borderType=cv2.BORDER_REFLECT)
    var = np.maximum(0.0, sq_mean - mean * mean)

    v_min = np.percentile(var, 5)
    v_max = np.percentile(var, 95)
    if v_max - v_min < 1e-6:
        return np.full_like(var, 0.5)

    v_norm = np.clip((var - v_min) / (v_max - v_min), 0.0, 1.0)
    return v_norm


def get_subimage_indices(
    height: int,
    width: int,
    L: int = 2,
    stego_key: Optional[str] = None,
    key_randomized: bool = False,
    exclude_header: bool = True,
) -> List[np.ndarray]:
    """
    Partitions the image grid into L^2 interleaved sub-images.
    If exclude_header is True, excludes the first HEADER_PIXELS from sub-images.
    """
    grid_coords = []
    if key_randomized and stego_key:
        seed = int(hashlib.sha256(stego_key.encode('utf-8')).hexdigest()[:8], 16)
        rng = np.random.RandomState(seed)
        all_pairs = [(r, c) for r in range(L) for c in range(L)]
        rng.shuffle(all_pairs)
        grid_coords = all_pairs
    else:
        for r in range(L):
            row_cols = list(range(L))
            if r % 2 == 1:
                row_cols.reverse()  # Horizontal zig-zag
            for c in row_cols:
                grid_coords.append((r, c))

    subimages = []
    R, C = np.indices((height, width))
    flat_indices = R * width + C

    for idx, (rk, ck) in enumerate(grid_coords):
        mask = (R % L == rk) & (C % L == ck)
        if exclude_header:
            mask = mask & (flat_indices >= HEADER_PIXELS)

        coords = np.argwhere(mask)
        if key_randomized and stego_key:
            sub_seed = (seed + idx * 7919) & 0xFFFFFFFF
            sub_rng = np.random.RandomState(sub_seed)
            perm = sub_rng.permutation(len(coords))
            coords = coords[perm]
        subimages.append(coords)

    return subimages


def count_directional_neighbors_4(
    D: np.ndarray,
    r: int,
    c: int,
    H: int,
    W: int,
) -> Tuple[int, int]:
    """4-Neighborhood rule: (r-1, c), (r+1, c), (r, c-1), (r, c+1)."""
    pos_count = 0
    neg_count = 0
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < H and 0 <= nc < W:
            val = D[nr, nc]
            if val == 1:
                pos_count += 1
            elif val == -1:
                neg_count += 1
    return pos_count, neg_count


def count_directional_neighbors_8_weighted(
    D: np.ndarray,
    r: int,
    c: int,
    H: int,
    W: int,
) -> float:
    """Novel 8-Neighborhood weighted voting: Orthogonal 1.0, Diagonal 0.5."""
    score = 0.0
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < H and 0 <= nc < W:
            score += 1.0 * float(D[nr, nc])

    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < H and 0 <= nc < W:
            score += 0.5 * float(D[nr, nc])

    return score


def split_message_segments(message_bits: np.ndarray, num_segments: int) -> List[np.ndarray]:
    """Splits message into num_segments equal (or nearly equal) segments."""
    total_len = len(message_bits)
    base_len = total_len // num_segments
    rem = total_len % num_segments

    segments = []
    curr = 0
    for i in range(num_segments):
        seg_len = base_len + (1 if i < rem else 0)
        segments.append(message_bits[curr:curr + seg_len])
        curr += seg_len

    return segments


def cmd_stego_embed(
    cover: np.ndarray,
    payload_data: bytes,
    password: Optional[str] = None,
    stego_key: Optional[str] = None,
    scheme: str = "HILL",
    L: int = 2,
    alpha: float = 9.0,
    adaptive_alpha: bool = False,
    neighborhood_8: bool = False,
    key_randomized: bool = False,
    h_trellis: int = 7,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Full CMD-Stego+ embedding pipeline with STC trellis coding.
    """
    cover = cover.astype(np.uint8)
    H, W = cover.shape

    # 1. Package payload
    frame_bytes = pack_payload(
        payload_bytes=payload_data,
        password=password,
        adaptive_alpha=adaptive_alpha,
        neighborhood_8=neighborhood_8,
        key_randomized=key_randomized,
    )
    frame_bits = bytes_to_bits(frame_bytes)
    total_bits = len(frame_bits)

    available_pixels = (H * W) - HEADER_PIXELS
    if total_bits > available_pixels:
        raise ValueError(
            f"Framed payload size ({total_bits} bits) exceeds available capacity ({available_pixels} bits)."
        )

    # 2. Embed 64-bit header in first 64 pixels
    Y = cover.copy()
    flat_y = Y.ravel()
    flat_y[:HEADER_PIXELS] = encode_header(flat_y[:HEADER_PIXELS], total_bits)
    Y = flat_y.reshape((H, W))

    # 3. Sub-image decomposition on remaining pixels
    effective_key = stego_key or password or "CMD_DEFAULT_KEY"
    subimages = get_subimage_indices(
        height=H,
        width=W,
        L=L,
        stego_key=effective_key,
        key_randomized=key_randomized,
        exclude_header=True,
    )
    num_sub = len(subimages)

    # 4. Message segment splitting
    segments = split_message_segments(frame_bits, num_sub)

    # Adaptive-alpha texture map
    if adaptive_alpha:
        tex_map = compute_texture_complexity(cover)
        alpha_min = max(2.0, alpha * 0.4)
        alpha_max = alpha * 1.8
        alpha_map = alpha_min + (alpha_max - alpha_min) * tex_map
    else:
        alpha_map = np.full((H, W), fill_value=alpha, dtype=np.float64)

    key_seed = int(hashlib.sha256(effective_key.encode('utf-8')).hexdigest()[:8], 16)

    # 5. Iterative embedding loop
    for t in range(num_sub):
        coords = subimages[t]
        seg_bits = segments[t]
        if len(seg_bits) == 0:
            continue

        r_idx = coords[:, 0]
        c_idx = coords[:, 1]
        cover_sub = Y[r_idx, c_idx]

        if t == 0:
            rho_plus_full, rho_minus_full = get_initial_costs(cover, scheme=scheme)
            sub_rho_p = rho_plus_full[r_idx, c_idx].copy()
            sub_rho_m = rho_minus_full[r_idx, c_idx].copy()
        else:
            D = Y.astype(np.int16) - cover.astype(np.int16)
            base_rho_p, base_rho_m = get_initial_costs(Y, scheme=scheme)
            sub_rho_p = base_rho_p[r_idx, c_idx].copy()
            sub_rho_m = base_rho_m[r_idx, c_idx].copy()

            for k in range(len(coords)):
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

        # Wet costs
        sub_rho_m[cover_sub == 0] = WET_COST
        sub_rho_p[cover_sub == 255] = WET_COST

        # Embed segment into sub-image
        stego_sub, dist = stc_embed(
            cover=cover_sub,
            rho_plus=sub_rho_p,
            rho_minus=sub_rho_m,
            message_bits=seg_bits,
            h=h_trellis,
            key_seed=key_seed + t * 31,
        )

        Y[r_idx, c_idx] = stego_sub

    # Execution statistics
    diff = Y.astype(np.int16) - cover.astype(np.int16)
    changes = np.sum(diff != 0)
    change_rate = float(changes) / float(H * W)
    bpp = float(total_bits) / float(H * W)

    stats = {
        'total_bits': total_bits,
        'bpp': bpp,
        'changes': int(changes),
        'change_rate': change_rate,
        'pos_changes': int(np.sum(diff == 1)),
        'neg_changes': int(np.sum(diff == -1)),
        'L': L,
        'alpha': alpha,
        'adaptive_alpha': adaptive_alpha,
        'neighborhood_8': neighborhood_8,
        'key_randomized': key_randomized,
        'scheme': scheme,
    }

    return Y, stats


def cmd_stego_extract(
    stego: np.ndarray,
    password: Optional[str] = None,
    stego_key: Optional[str] = None,
    L: int = 2,
    key_randomized: bool = False,
    h_trellis: int = 7,
    known_total_bits: Optional[int] = None,
) -> Tuple[bytes, Dict[str, Any]]:
    """
    Extracts and authenticates payload from stego image Y.
    Round-trip bit-exact extraction using STC syndrome parity check.
    """
    stego = stego.astype(np.uint8)
    H, W = stego.shape
    effective_key = stego_key or password or "CMD_DEFAULT_KEY"
    key_seed = int(hashlib.sha256(effective_key.encode('utf-8')).hexdigest()[:8], 16)

    # Determine total bits
    if known_total_bits is not None:
        total_bits = known_total_bits
    else:
        flat_stego = stego.ravel()
        decoded_bits = decode_header(flat_stego[:HEADER_PIXELS])
        if decoded_bits is None:
            raise ValueError("No valid CMD-Stego+ header detected in stego image.")
        total_bits = decoded_bits

    subimages = get_subimage_indices(
        height=H,
        width=W,
        L=L,
        stego_key=effective_key,
        key_randomized=key_randomized,
        exclude_header=True,
    )
    num_sub = len(subimages)

    segments_lengths = []
    base_len = total_bits // num_sub
    rem = total_bits % num_sub
    for i in range(num_sub):
        segments_lengths.append(base_len + (1 if i < rem else 0))

    extracted_segments = []
    for t in range(num_sub):
        coords = subimages[t]
        seg_len = segments_lengths[t]
        if seg_len == 0:
            continue
        r_idx = coords[:, 0]
        c_idx = coords[:, 1]
        stego_sub = stego[r_idx, c_idx]
        seg_bits = stc_extract(
            stego=stego_sub,
            m_len=seg_len,
            h=h_trellis,
            key_seed=key_seed + t * 31,
        )
        extracted_segments.append(seg_bits)

    full_frame_bits = np.concatenate(extracted_segments)
    frame_bytes = bits_to_bytes(full_frame_bits)

    plaintext, metadata = unpack_payload(frame_bytes, password=password)
    return plaintext, metadata
