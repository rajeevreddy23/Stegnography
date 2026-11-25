"""
Security and Cryptographic Packaging Module for CMD-Stego+.
Provides PBKDF2-HMAC-SHA256 key derivation, AES-256-GCM authenticated encryption,
CRC32 data integrity checking, and bitstream framing.
"""

import os
import struct
import zlib
from typing import Tuple, Dict, Any
import numpy as np
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# Magic identifier for CMD-Stego+ bitstreams: 'CMDS'
MAGIC_HEADER = b'CMDS'
HEADER_VERSION = 1

# Flag bitmasks
FLAG_ENCRYPTED = 0x01
FLAG_ADAPTIVE_ALPHA = 0x02
FLAG_NEIGHBORHOOD_8 = 0x04
FLAG_KEY_RANDOMIZED = 0x08


class SecurityError(Exception):
    """Base class for security/framing exceptions."""
    pass


class DecryptionError(SecurityError):
    """Raised when authentication tag or key derivation fails."""
    pass


class ChecksumError(SecurityError):
    """Raised when CRC32 checksum verification fails."""
    pass


class InvalidHeaderError(SecurityError):
    """Raised when the framing magic or version is invalid."""
    pass


def derive_key(password: str, salt: bytes, iterations: int = 100_000) -> bytes:
    """
    Derive a 256-bit symmetric encryption key from password and salt using PBKDF2-HMAC-SHA256.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(password.encode('utf-8'))


def pack_payload(
    payload_bytes: bytes,
    password: str = None,
    adaptive_alpha: bool = False,
    neighborhood_8: bool = False,
    key_randomized: bool = False,
) -> bytes:
    """
    Encapsulates raw payload bytes into an authenticated bitstream frame.
    If password is provided, encrypts payload using AES-256-GCM.
    
    Frame Layout:
    - 4 bytes: Magic 'CMDS'
    - 1 byte:  Version (1)
    - 1 byte:  Flags bitmask
    - 4 bytes: Uncompressed / Plaintext Payload Length (Big Endian)
    - 4 bytes: CRC32 checksum of plaintext
    - If FLAG_ENCRYPTED:
        - 16 bytes: PBKDF2 Salt
        - 12 bytes: AES-GCM Nonce (IV)
        - 16 bytes: AES-GCM Tag
        - N bytes:  Ciphertext
    - Else:
        - N bytes:  Raw Payload
    """
    flags = 0
    if adaptive_alpha:
        flags |= FLAG_ADAPTIVE_ALPHA
    if neighborhood_8:
        flags |= FLAG_NEIGHBORHOOD_8
    if key_randomized:
        flags |= FLAG_KEY_RANDOMIZED

    payload_crc = zlib.crc32(payload_bytes) & 0xFFFFFFFF
    payload_len = len(payload_bytes)

    if password:
        flags |= FLAG_ENCRYPTED
        salt = os.urandom(16)
        nonce = os.urandom(12)
        key = derive_key(password, salt)
        aesgcm = AESGCM(key)
        # Encrypt with Associated Data (Header prefix for tamper proofing)
        aad = MAGIC_HEADER + bytes([HEADER_VERSION, flags]) + struct.pack('>II', payload_len, payload_crc)
        # AESGCM.encrypt appends 16-byte tag to the ciphertext
        encrypted_data = aesgcm.encrypt(nonce, payload_bytes, aad)
        ciphertext = encrypted_data[:-16]
        tag = encrypted_data[-16:]

        header = (
            MAGIC_HEADER +
            bytes([HEADER_VERSION, flags]) +
            struct.pack('>II', payload_len, payload_crc) +
            salt +
            nonce +
            tag
        )
        return header + ciphertext
    else:
        header = (
            MAGIC_HEADER +
            bytes([HEADER_VERSION, flags]) +
            struct.pack('>II', payload_len, payload_crc)
        )
        return header + payload_bytes


def unpack_payload(
    frame_bytes: bytes,
    password: str = None,
) -> Tuple[bytes, Dict[str, Any]]:
    """
    Parses and authenticates a frame, decrypting payload if encrypted.
    Returns (plaintext_bytes, metadata_dict).
    """
    if len(frame_bytes) < 14:
        raise InvalidHeaderError("Frame too short to contain valid CMD-Stego header.")

    magic = frame_bytes[:4]
    if magic != MAGIC_HEADER:
        raise InvalidHeaderError(f"Invalid magic identifier: {magic!r}. Expected {MAGIC_HEADER!r}.")

    version = frame_bytes[4]
    flags = frame_bytes[5]
    payload_len, payload_crc = struct.unpack('>II', frame_bytes[6:14])

    metadata = {
        'version': version,
        'flags': flags,
        'encrypted': bool(flags & FLAG_ENCRYPTED),
        'adaptive_alpha': bool(flags & FLAG_ADAPTIVE_ALPHA),
        'neighborhood_8': bool(flags & FLAG_NEIGHBORHOOD_8),
        'key_randomized': bool(flags & FLAG_KEY_RANDOMIZED),
        'payload_length': payload_len,
    }

    if metadata['encrypted']:
        if not password:
            raise DecryptionError("Payload is encrypted but no password was provided.")
        if len(frame_bytes) < 14 + 16 + 12 + 16:
            raise InvalidHeaderError("Encrypted frame is truncated.")

        offset = 14
        salt = frame_bytes[offset:offset+16]; offset += 16
        nonce = frame_bytes[offset:offset+12]; offset += 12
        tag = frame_bytes[offset:offset+16]; offset += 16
        ciphertext = frame_bytes[offset:]

        aad = MAGIC_HEADER + bytes([version, flags]) + struct.pack('>II', payload_len, payload_crc)
        key = derive_key(password, salt)
        aesgcm = AESGCM(key)

        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext + tag, aad)
        except Exception as e:
            raise DecryptionError(f"Authentication failed: Incorrect password or corrupted stego data. ({e})")
    else:
        plaintext = frame_bytes[14:14 + payload_len]

    # Verify checksum
    calc_crc = zlib.crc32(plaintext) & 0xFFFFFFFF
    if calc_crc != payload_crc:
        raise ChecksumError(f"CRC32 mismatch: calculated {calc_crc:#010x}, expected {payload_crc:#010x}.")

    return plaintext, metadata


def bytes_to_bits(data: bytes) -> np.ndarray:
    """Converts a bytes object into a 1D numpy array of 0s and 1s (MSB first per byte)."""
    byte_arr = np.frombuffer(data, dtype=np.uint8)
    return np.unpackbits(byte_arr)


def bits_to_bytes(bits: np.ndarray) -> bytes:
    """Converts a 1D numpy array of bits into bytes (MSB first per byte)."""
    # Ensure length is multiple of 8
    rem = len(bits) % 8
    if rem != 0:
        bits = np.pad(bits, (0, 8 - rem), 'constant')
    return np.packbits(bits).tobytes()
