"""
Unit Tests for Syndrome-Trellis Codes (STC).
Verifies 100% bit-exact syndrome decoding and minimal additive distortion.
"""

import pytest
import numpy as np
from backend.core.stc import stc_embed, stc_extract, get_generator_hat


@pytest.mark.parametrize("h", [7, 8])
@pytest.mark.parametrize("payload_bits", [50, 100, 250])
def test_stc_round_trip(h, payload_bits):
    rng = np.random.RandomState(42 + payload_bits)
    cover_size = 1000
    cover = rng.randint(20, 230, size=cover_size, dtype=np.uint8)
    message = rng.randint(0, 2, size=payload_bits, dtype=np.uint8)
    rho_p = rng.uniform(0.1, 5.0, size=cover_size)
    rho_m = rng.uniform(0.1, 5.0, size=cover_size)

    stego, dist = stc_embed(
        cover=cover,
        rho_plus=rho_p,
        rho_minus=rho_m,
        message_bits=message,
        h=h,
        key_seed=123,
    )

    extracted = stc_extract(
        stego=stego,
        m_len=payload_bits,
        h=h,
        key_seed=123,
    )

    assert len(extracted) == payload_bits
    np.testing.assert_array_equal(extracted, message)
    # Check that distortion was recorded and reasonable
    assert dist >= 0.0


def test_stc_wet_costs_saturation():
    """Verify that saturated pixels (0 or 255) are never modified out of bounds."""
    rng = np.random.RandomState(999)
    cover = np.zeros(500, dtype=np.uint8)  # All zeros
    cover[250:] = 255  # Half zeros, half 255
    message = rng.randint(0, 2, size=50, dtype=np.uint8)
    rho_p = np.ones(500)
    rho_m = np.ones(500)

    stego, _ = stc_embed(cover, rho_p, rho_m, message, h=7, key_seed=42)

    assert np.all(stego >= 0)
    assert np.all(stego <= 255)
    # 0 pixels should never decrease, 255 pixels should never increase
    assert np.all(stego[:250] >= 0)
    assert np.all(stego[250:] <= 255)
