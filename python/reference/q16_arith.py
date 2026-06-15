"""
Q16.16 fixed-point arithmetic helpers.

These match the bit-exact behavior of the VHDL cores in hdl/.
All multiplications use signed 64-bit intermediate then >> 16 shift.
All additions saturate to signed 32-bit range.
"""

import numpy as np

FRAC_BITS = 16
SCALE     = 1 << FRAC_BITS         # 65536
MAX_Q     = (1 << 31) - 1          # max signed 32-bit
MIN_Q     = -(1 << 31)             # min signed 32-bit


def to_fixed(x):
    """Convert float to Q16.16 signed 32-bit integer (rounded)."""
    return int(round(x * SCALE))


def to_float(q):
    """Convert Q16.16 integer back to float."""
    return q / SCALE


def fixed_mul(a, b):
    """
    Multiply two Q16.16 integers.
    Matches VHDL behavior: signed 64-bit product, >> 16, saturate to 32-bit.
    """
    product = a * b
    result  = product >> FRAC_BITS
    return int(np.clip(result, MIN_Q, MAX_Q))


def fixed_add(a, b):
    """Add two Q16.16 integers with saturation."""
    return int(np.clip(a + b, MIN_Q, MAX_Q))


def fixed_sub(a, b):
    """Subtract two Q16.16 integers with saturation."""
    return int(np.clip(a - b, MIN_Q, MAX_Q))
