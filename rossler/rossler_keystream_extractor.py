"""
================================================================================
FILE: rossler_keystream_extractor.py
SYSTEM: Rössler System — Keystream Extraction Module
================================================================================
DESCRIPTION:
    Converts Rössler state variables (x, y, z) into a 16-bit keystream
    using FIXED normalization bounds (phase-space projection method).

    Critical: Uses fixed theoretical attractor bounds — NOT data-driven
    min/max — so transmitter and receiver produce IDENTICAL keystreams.

HOW TO RUN:
    from rossler_keystream_extractor import RosslerKeystreamExtractor
    extractor = RosslerKeystreamExtractor()
    keystream = extractor.extract(x_arr, y_arr, z_arr)
================================================================================
"""

import numpy as np

# ── Fixed attractor bounds for Rössler spiral ─────────────────────────────────
ROSSLER_X_BOUND = 12.0   # x in approximately [-12, +12]
ROSSLER_Y_BOUND = 12.0   # y in approximately [-12, +12]
ROSSLER_Z_BOUND = 25.0   # z in approximately [0, +25] — offset handled below


class RosslerKeystreamExtractor:
    """
    Extracts a 16-bit keystream from Rössler state variables.
    Uses fixed normalization bounds for deterministic, identical output
    on both transmitter and receiver boards.
    """

    def __init__(self):
        pass

    def _normalize_fixed(self, arr, bound, offset=0.0):
        """
        Normalize using fixed bounds: maps [offset-bound, offset+bound] → [-1,+1].
        Clips values outside the expected attractor range.
        """
        clipped = np.clip(arr, offset - bound, offset + bound)
        return (clipped - offset) / bound

    def _to_int16(self, normalized_arr):
        """Scale [-1,+1] to int16. Floor matches hardware truncation."""
        return np.floor(normalized_arr * 32767.0).astype(np.int16)

    def _bit_mix(self, k):
        """Feistel-style bit rotation for final whitening."""
        ku    = k.view(np.uint16)
        mixed = (np.left_shift(ku, 5) | np.right_shift(ku, 11)) ^ \
                (np.left_shift(ku, 11) | np.right_shift(ku, 5))
        return mixed.view(np.int16)

    def _validate_keystream(self, keystream):
        """Statistical quality check."""
        ks_float   = keystream.astype(np.float64)
        ks_uint    = keystream.view(np.uint16)
        set_bits   = np.unpackbits(ks_uint.view(np.uint8)).sum()
        bit_ratio  = set_bits / (len(ks_uint) * 16)
        print(f"[RosslerKeystream] Quality: mean={np.mean(ks_float):.1f}, "
              f"std={np.std(ks_float):.1f}, bit_ratio={bit_ratio:.3f}")

    def extract(self, x_arr, y_arr, z_arr):
        """
        Convert Rössler state variables to 16-bit keystream.
        Fixed-bound normalization ensures identical output on both boards.
        z uses offset=12.5 because Rössler z lives in [0, ~25].
        """
        assert len(x_arr) == len(y_arr) == len(z_arr)

        # ── Fixed-bound normalization ──────────────────────────────────────
        x_norm = self._normalize_fixed(x_arr, ROSSLER_X_BOUND, offset=0.0)
        y_norm = self._normalize_fixed(y_arr, ROSSLER_Y_BOUND, offset=0.0)
        z_norm = self._normalize_fixed(z_arr, ROSSLER_Z_BOUND, offset=12.5)

        # ── Convert to int16 ───────────────────────────────────────────────
        kx = self._to_int16(x_norm)
        ky = self._to_int16(y_norm)
        kz = self._to_int16(z_norm)

        # ── XOR mix all three state variables ─────────────────────────────
        keystream = np.bitwise_xor(np.bitwise_xor(kx, ky), kz)

        # ── Bit mixing ────────────────────────────────────────────────────
        keystream = self._bit_mix(keystream)
        self._validate_keystream(keystream)

        return keystream
