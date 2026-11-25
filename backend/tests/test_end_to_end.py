"""
End-to-End Integration Tests for CMD-Stego+.
Verifies 100% bit-exact round-trip embedding and extraction across relative payloads:
0.05, 0.10, 0.20, 0.30, 0.40, and 0.50 bpp.
Tests with encryption, adaptive-alpha, key-randomization, and 8-neighborhood voting.
"""

import pytest
import numpy as np
import os
from backend.core.cmd_stego import cmd_stego_embed, cmd_stego_extract


@pytest.mark.parametrize("payload_bpp", [0.05, 0.10, 0.20, 0.30, 0.40, 0.50])
def test_full_round_trip_payloads(payload_bpp):
    """
    Verifies that embedding random payloads from 0.05 to 0.50 bpp round-trips with 0 bit errors.
    """
    H, W = 128, 128
    total_pixels = H * W
    cover = np.random.randint(20, 235, (H, W), dtype=np.uint8)

    # Calculate raw payload byte size to match target bpp after framing
    # Overhead is ~48 bytes for encrypted frame + 8 bytes header = 56 bytes
    target_total_bits = int(payload_bpp * total_pixels)
    target_total_bytes = target_total_bits // 8
    raw_payload_len = max(8, target_total_bytes - 60)

    # Generate random binary message bytes
    message = os.urandom(raw_payload_len)
    password = f"Pass_{int(payload_bpp*100)}bpp"
    stego_key = f"Key_{int(payload_bpp*100)}"

    # 1. Embed
    stego, stats = cmd_stego_embed(
        cover=cover,
        payload_data=message,
        password=password,
        stego_key=stego_key,
        scheme="HILL",
        L=2,
        alpha=9.0,
        adaptive_alpha=True,
        neighborhood_8=True,
        key_randomized=True,
    )

    assert stego.shape == (H, W)
    assert stats['changes'] > 0
    assert stats['change_rate'] > 0.0

    # 2. Extract
    recovered, meta = cmd_stego_extract(
        stego=stego,
        password=password,
        stego_key=stego_key,
        L=2,
        key_randomized=True,
    )

    # 3. Assert bit-exact identity
    assert len(recovered) == len(message), f"Length mismatch: {len(recovered)} vs {len(message)}"
    assert recovered == message, f"Decrypted payload mismatch at payload {payload_bpp} bpp!"
    assert meta['encrypted'] is True
    assert meta['adaptive_alpha'] is True
    assert meta['neighborhood_8'] is True
    assert meta['key_randomized'] is True


def test_round_trip_plain_unencrypted():
    """Verifies round-trip with unencrypted payload (plain mode)."""
    cover = np.random.randint(20, 235, (128, 128), dtype=np.uint8)
    message = b"Testing Plain Unencrypted Steganography Data Transfer!"

    stego, stats = cmd_stego_embed(
        cover=cover,
        payload_data=message,
        password=None,
        stego_key="SharedKey123",
        scheme="HILL",
        L=2,
        alpha=9.0,
        adaptive_alpha=False,
        neighborhood_8=False,
        key_randomized=False,
    )

    recovered, meta = cmd_stego_extract(
        stego=stego,
        password=None,
        stego_key="SharedKey123",
        L=2,
        key_randomized=False,
    )

    assert recovered == message
    assert meta['encrypted'] is False


def test_round_trip_wrong_password_fails():
    """Verifies that an incorrect password fails authentication and raises exception."""
    cover = np.random.randint(20, 235, (128, 128), dtype=np.uint8)
    message = b"Secret Payload Protected By AES-GCM"

    stego, _ = cmd_stego_embed(
        cover=cover,
        payload_data=message,
        password="SuperPassword123",
        stego_key="Key",
        scheme="HILL",
    )

    with pytest.raises(Exception):
        cmd_stego_extract(
            stego=stego,
            password="WrongPassword999",
            stego_key="Key",
        )
