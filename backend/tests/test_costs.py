"""
Unit Tests for Distortion Cost Functions (HILL, S-UNIWARD, WOW).
"""

import pytest
import numpy as np
from backend.core.costs import (
    compute_hill_costs,
    compute_suniward_costs,
    compute_wow_costs,
    get_initial_costs,
    WET_COST,
)


def test_hill_costs():
    img = np.random.randint(0, 256, (64, 64), dtype=np.uint8)
    C = compute_hill_costs(img)
    assert C.shape == (64, 64)
    assert np.all(C > 0)
    assert not np.any(np.isnan(C))
    assert not np.any(np.isinf(C))


def test_suniward_costs():
    img = np.random.randint(0, 256, (64, 64), dtype=np.uint8)
    C = compute_suniward_costs(img)
    assert C.shape == (64, 64)
    assert np.all(C > 0)


def test_wow_costs():
    img = np.random.randint(0, 256, (64, 64), dtype=np.uint8)
    C = compute_wow_costs(img)
    assert C.shape == (64, 64)
    assert np.all(C > 0)


def test_wet_cost_boundary():
    img = np.full((32, 32), 128, dtype=np.uint8)
    img[0, 0] = 0
    img[1, 1] = 255

    rho_p, rho_m = get_initial_costs(img, scheme="HILL")
    # For pixel value 0: modification -1 forbidden
    assert rho_m[0, 0] >= WET_COST
    assert rho_p[0, 0] < WET_COST

    # For pixel value 255: modification +1 forbidden
    assert rho_p[1, 1] >= WET_COST
    assert rho_m[1, 1] < WET_COST
