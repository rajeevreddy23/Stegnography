"""
Unit Tests for Cryptographic Security, AES-256-GCM, CRC32, and Framing.
"""

import pytest
from backend.core.security import (
    pack_payload,
    unpack_payload,
    derive_key,
    DecryptionError,
    ChecksumError,
    InvalidHeaderError,
)


def test_encryption_round_trip():
    secret_msg = b"Final-year Project Secret: CMD-Stego+ Adaptive Clustering 2026!"
    password = "MasterPassword123!"

    frame = pack_payload(secret_msg, password=password, adaptive_alpha=True, neighborhood_8=True)
    recovered, meta = unpack_payload(frame, password=password)

    assert recovered == secret_msg
    assert meta['encrypted'] is True
    assert meta['adaptive_alpha'] is True
    assert meta['neighborhood_8'] is True


def test_plain_round_trip():
    plain_msg = b"Unencrypted payload data stream."
    frame = pack_payload(plain_msg, password=None)
    recovered, meta = unpack_payload(frame, password=None)

    assert recovered == plain_msg
    assert meta['encrypted'] is False


def test_incorrect_password_raises():
    secret_msg = b"Super confidential payload."
    frame = pack_payload(secret_msg, password="CorrectPassword")

    with pytest.raises(DecryptionError):
        unpack_payload(frame, password="WrongPassword")


def test_tampering_corrupted_ciphertext():
    secret_msg = b"Authenticity verified payload."
    frame = bytearray(pack_payload(secret_msg, password="SecurePassword"))

    # Corrupt a byte in ciphertext
    frame[-5] ^= 0xFF

    with pytest.raises(DecryptionError):
        unpack_payload(bytes(frame), password="SecurePassword")


def test_invalid_header_magic():
    bad_frame = b"BADM" + b"\x00" * 30
    with pytest.raises(InvalidHeaderError):
        unpack_payload(bad_frame)
