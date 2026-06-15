"""
Reference encryptor — transmitter-side chaotic stream cipher.

Works with either ChuaGenerator or RosslerGenerator.
Performs bitwise XOR encryption:   C[n] = P[n] ⊕ K[n]

Outputs:
    - encrypted .wav
    - keystream .npy  (uint16, exposed for verification)
    - drive_signal .npy  (Q16.16 int32 x_state for receiver sync)
    - secret_key .npy  (initial conditions dict)
"""

import os
import sys
import numpy as np
import scipy.io.wavfile as wavfile

sys.path.insert(0, os.path.dirname(__file__))
from chua_generator    import ChuaGenerator
from rossler_generator import RosslerGenerator


def _load_audio_mono(filepath):
    """Load mono 16-bit PCM. Stereo → take left channel."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Audio file not found: {filepath}")
    sr, samples = wavfile.read(filepath)
    if samples.ndim == 2:
        print(f"  Stereo detected — using left channel only")
        samples = samples[:, 0]
    if samples.dtype != np.int16:
        samples = samples.astype(np.int16)
    return sr, samples


def encrypt(input_wav, system, output_dir, x0=None, y0=None, z0=None,
            role='master'):
    """
    Encrypt input_wav with chaotic XOR stream cipher.

    Args:
        input_wav  : path to mono/stereo 16-bit PCM .wav file
        system     : 'chua' or 'rossler'
        output_dir : where to write encrypted .wav and supporting .npy files
        x0,y0,z0   : initial conditions (None → VHDL defaults)
        role       : 'master' or 'slave' (Rössler only — sets IC defaults)

    Returns:
        dict with paths and arrays for downstream decryptor.
    """
    os.makedirs(output_dir, exist_ok=True)

    print(f"=== {system.upper()} encryptor ===")
    sr, plaintext = _load_audio_mono(input_wav)
    n = len(plaintext)
    print(f"  Loaded {n} samples @ {sr} Hz ({n/sr:.2f} s)")

    # ─── Build generator ─────────────────────────────────────────────────────
    if system == 'chua':
        gen = ChuaGenerator(x0=x0, y0=y0, z0=z0)
    elif system == 'rossler':
        gen = RosslerGenerator(role=role, x0=x0, y0=y0, z0=z0)
    else:
        raise ValueError(f"Unknown system: {system}")

    # ─── Generate chaotic trajectory ─────────────────────────────────────────
    print(f"  Generating {n} chaotic samples...")
    x_arr, y_arr, z_arr, x_int = gen.generate(n)

    # ─── Extract keystream (matches VHDL: x_state[23:8]) ─────────────────────
    keystream = gen.extract_keystream(x_int)

    # ─── XOR encrypt ─────────────────────────────────────────────────────────
    plain_u   = plaintext.view(np.uint16)
    cipher_u  = np.bitwise_xor(plain_u, keystream)
    ciphertext = cipher_u.view(np.int16)

    # ─── Save outputs ────────────────────────────────────────────────────────
    base       = os.path.splitext(os.path.basename(input_wav))[0]
    prefix     = f"{system}_{base}"
    enc_path   = os.path.join(output_dir, f"{prefix}_encrypted.wav")
    drive_path = os.path.join(output_dir, f"{prefix}_drive.npy")
    ks_path    = os.path.join(output_dir, f"{prefix}_keystream.npy")
    key_path   = os.path.join(output_dir, f"{prefix}_secret_key.npy")

    wavfile.write(enc_path, sr, ciphertext)
    np.save(drive_path, x_int)        # Q16.16 int x trajectory
    np.save(ks_path, keystream)       # uint16 keystream
    np.save(key_path, np.array({
        'system': system,
        'x0': x_arr[0], 'y0': y_arr[0], 'z0': z_arr[0],
        'role': role,
    }, dtype=object))

    print(f"  Saved: {os.path.basename(enc_path)}")

    return {
        'sample_rate': sr,
        'plaintext'  : plaintext,
        'ciphertext' : ciphertext,
        'keystream'  : keystream,
        'x_int'      : x_int,
        'enc_path'   : enc_path,
        'drive_path' : drive_path,
        'ks_path'    : ks_path,
        'key_path'   : key_path,
    }
