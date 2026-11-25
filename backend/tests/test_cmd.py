"""
Unit Tests for CMD Engine, Lattice Decomposition, and Directional Voting.
"""

import numpy as np
import pytest
from backend.core.cmd_stego import (
    get_subimage_indices,
    compute_texture_complexity,
    count_directional_neighbors_4,
    count_directional_neighbors_8_weighted,
)


def test_lattice_decomposition_coverage():
    H, W, L = 64, 64, 2
    subimages = get_subimage_indices(H, W, L=L, exclude_header=False)
    assert len(subimages) == L * L

    all_coords = np.vstack(subimages)
    # Check that all pixels are accounted for exactly once
    assert len(all_coords) == H * W
    unique_coords = np.unique(all_coords[:, 0] * W + all_coords[:, 1])
    assert len(unique_coords) == H * W


def test_texture_complexity_range():
    img = np.random.randint(0, 256, (128, 128), dtype=np.uint8)
    tex = compute_texture_complexity(img)
    assert tex.shape == (128, 128)
    assert np.min(tex) >= 0.0
    assert np.max(tex) <= 1.0


def test_neighborhood_voting_rules():
    D = np.zeros((5, 5), dtype=np.int16)
    # Set neighbors around (2, 2)
    D[1, 2] = 1   # up: +1
    D[3, 2] = 1   # down: +1
    D[2, 1] = -1  # left: -1

    pos_c, neg_c = count_directional_neighbors_4(D, 2, 2, 5, 5)
    assert pos_c == 2
    assert neg_c == 1

    # Test 8-neighbor weighted voting
    D[1, 1] = 1   # top-left diag: +1 (weight 0.5)
    score = count_directional_neighbors_8_weighted(D, 2, 2, 5, 5)
    # expected: (1*1 + 1*1 - 1*1) + 0.5*1 = 1.5
    assert score == pytest.approx(1.5)
