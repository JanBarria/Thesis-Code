"""
================================================================================
FILE: chua_keystream_extractor.py
SYSTEM: Chua Circuit — Keystream Extraction Module
================================================================================
DESCRIPTION:
    Converts raw Chua chaotic state variables (x, y, z) into a 16-bit integer
    keystream compatible with PCM audio XOR encryption.

    Method: STATE-VARIABLE SAMPLING with FIXED normalization bounds.
    Critical fix: normalization uses FIXED theoretical attractor bounds
    (not data-driven min/max), ensuring the transmitter and receiver
    produce IDENTICAL keystreams from identical state variables.

HOW TO RUN:
    from chua_keystream_extractor import ChuaKeystreamExtractor
    extractor = ChuaKeystreamExtractor()
    keystream = extractor.extract(x_arr, y_arr, z_arr)
================================================================================
"""

import numpy as np

# ── Fixed attractor bounds for Chua double-scroll ─────────────────────────────
# These are the theoretical bounds of the Chua double-scroll attractor.
# Using fixed bounds (not data-driven) ensures transmitter and receiver
# produce IDENTICAL keystreams — critical for correct decryption.
CHUA_X_BOUND = 3.0    # x oscillates in approximately [-3, +3]
CHUA_Y_BOUND = 0.4    # y oscillates in approximately [-0.4, +0.4]
CHUA_Z_BOUND = 4.5    # z oscillates in approximately [-4.5, +4.5]


class ChuaKeystreamExtractor:
    """
    Extracts a 16-bit integer keystream from Chua state variables.
    Uses fixed normalization bounds to guarantee identical keystreams
    on both transmitter and receiver sides.
    """

    def __init__(self, use_xyz_mix=True):
        self.use_xyz_mix = use_xyz_mix

    def _normalize_fixed(self, arr, bound):
        """
        Normalize using fixed theoretical bound: maps [-bound, +bound] → [-1, +1].
        Values outside bounds are clipped. This is deterministic and identical
        on both transmitter and receiver regardless of transient differences.
        """
        clipped = np.clip(arr, -bound, bound)
        return clipped / bound   # maps [-bound,+bound] → [-1,+1]

    def _to_int16(self, normalized_arr):
        """Scale [-1,+1] float to int16. Floor matches hardware truncation."""
        scaled = normalized_arr * 32767.0
        return np.floor(scaled).astype(np.int16)

    def _bit_mix(self, k):
        """Bit-rotation XOR mixing for uniform distribution across all bits."""
        ku    = k.view(np.uint16)
        mixed = (np.left_shift(ku, 3) | np.right_shift(ku, 13)) ^ \
                (np.left_shift(ku, 7) | np.right_shift(ku, 9))
        return mixed.view(np.int16)

    def _validate_keystream(self, keystream):
        """Statistical quality checks."""
        ks_float  = keystream.astype(np.float64)
        mean_val  = np.mean(ks_float)
        std_val   = np.std(ks_float)
        ks_uint   = keystream.view(np.uint16)
        total_bits = len(ks_uint) * 16
        set_bits   = np.unpackbits(ks_uint.view(np.uint8)).sum()
        bit_ratio  = set_bits / total_bits

        print(f"[ChuaKeystream] Quality: mean={mean_val:.1f}, "
              f"std={std_val:.1f}, bit_ratio={bit_ratio:.3f}")

    def extract(self, x_arr, y_arr, z_arr):
        """
        Convert Chua state variables to 16-bit keystream.
        Uses fixed normalization bounds — results are IDENTICAL on
        transmitter and receiver for the same state variable inputs.
        """
        assert len(x_arr) == len(y_arr) == len(z_arr)

        # ── Fixed-bound normalization (deterministic) ──────────────────────
        x_norm = self._normalize_fixed(x_arr, CHUA_X_BOUND)
        y_norm = self._normalize_fixed(y_arr, CHUA_Y_BOUND)
        z_norm = self._normalize_fixed(z_arr, CHUA_Z_BOUND)

        # ── Convert to int16 ───────────────────────────────────────────────
        kx = self._to_int16(x_norm)
        ky = self._to_int16(y_norm)
        kz = self._to_int16(z_norm)

        # ── XOR-mix all three variables ────────────────────────────────────
        if self.use_xyz_mix:
            keystream = np.bitwise_xor(np.bitwise_xor(kx, ky), kz)
        else:
            keystream = kx

        # ── Bit mixing ────────────────────────────────────────────────────
        keystream = self._bit_mix(keystream)
        self._validate_keystream(keystream)

        return keystream
