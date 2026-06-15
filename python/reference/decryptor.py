"""
Reference decryptor — receiver-side chaotic stream cipher.

Two sync modes:

    PRESHARED key mode (default):
        Receiver regenerates the same trajectory from the secret key
        (matching initial conditions and parameters). Decryption succeeds
        as long as both sides use the same VHDL/Python parameters.

    PECORA_CARROLL mode (true subsystem driving — matches new VHDL):
        Receiver runs as 'slave' generator with role='slave' initial conditions
        (deliberately different from master). At each step, the slave's x
        variable is substituted by the received x_drive sample. Slave's y, z
        then evolve to synchronize with master via the chaotic dynamics.

The slave's keystream is extracted from the substituted x — which equals
the master's x — so the keystream matches and decryption succeeds.

Metrics computed:
    Pearson r, BER, MSE, SNR, sync error.
"""

import os
import sys
import numpy as np
import scipy.io.wavfile as wavfile

sys.path.insert(0, os.path.dirname(__file__))
from chua_generator    import ChuaGenerator
from rossler_generator import RosslerGenerator


def _load_audio_mono(filepath):
    sr, samples = wavfile.read(filepath)
    if samples.ndim == 2:
        samples = samples[:, 0]
    return sr, samples.astype(np.int16)


def decrypt(encrypted_wav, original_wav, drive_npy, system,
            sync_mode='preshared', role='slave',
            x0=None, y0=None, z0=None):
    """
    Decrypt encrypted_wav using chaotic synchronization.

    Args:
        encrypted_wav : path to ciphertext .wav
        original_wav  : path to original plaintext .wav (for metric comparison)
        drive_npy     : path to .npy file containing transmitter's x_int trajectory
        system        : 'chua' or 'rossler'
        sync_mode     : 'preshared' or 'pecora_carroll'
        role          : 'master' or 'slave' (Rössler ICs)
        x0,y0,z0      : override ICs (default: VHDL master ICs for preshared)

    Returns:
        dict of metrics + decrypted samples.
    """
    print(f"=== {system.upper()} decryptor [{sync_mode}] ===")

    sr_c, ciphertext = _load_audio_mono(encrypted_wav)
    _,    original   = _load_audio_mono(original_wav)
    x_drive_int      = np.load(drive_npy).astype(np.int64)

    n = min(len(ciphertext), len(original), len(x_drive_int))
    ciphertext  = ciphertext[:n]
    original    = original[:n]
    x_drive_int = x_drive_int[:n]

    # ─── Build generator ─────────────────────────────────────────────────────
    if system == 'chua':
        # Preshared: use same ICs as transmitter (x0=0.1, y0=0, z0=0)
        # PC mode: Chua's PC sync drives x_s0 substitution in VHDL
        if sync_mode == 'preshared':
            gen = ChuaGenerator(x0=x0, y0=y0, z0=z0)
        else:
            gen = ChuaGenerator(x0=x0, y0=y0, z0=z0)
    elif system == 'rossler':
        if sync_mode == 'preshared':
            # Same ICs as master (1,1,1)
            gen = RosslerGenerator(role='master', x0=x0, y0=y0, z0=z0)
        else:
            # Slave gets different ICs (1, 0.5, 1.5); x driven by master
            gen = RosslerGenerator(role=role,
                                   x0=x0, y0=y0, z0=z0)
    else:
        raise ValueError(f"Unknown system: {system}")

    # ─── Regenerate trajectory ───────────────────────────────────────────────
    if sync_mode == 'pecora_carroll':
        x_arr, y_arr, z_arr, x_int = gen.generate(n, x_drive_int_arr=x_drive_int)
    else:
        x_arr, y_arr, z_arr, x_int = gen.generate(n)

    keystream = gen.extract_keystream(x_int)

    # ─── XOR decrypt ─────────────────────────────────────────────────────────
    cipher_u  = ciphertext.view(np.uint16)
    plain_u   = np.bitwise_xor(cipher_u, keystream)
    decrypted = plain_u.view(np.int16)

    # ─── Metrics ─────────────────────────────────────────────────────────────
    orig_f = original.astype(np.float64)
    dec_f  = decrypted.astype(np.float64)

    if orig_f.std() < 1e-9 or dec_f.std() < 1e-9:
        pearson_r = 0.0
    else:
        pearson_r = float(np.corrcoef(orig_f, dec_f)[0, 1])

    # Bit error rate (16 bits per sample)
    diff_bits  = np.bitwise_xor(original.view(np.uint16),
                                 decrypted.view(np.uint16))
    bit_errors = int(np.unpackbits(diff_bits.view(np.uint8)).sum())
    total_bits = len(original) * 16
    ber        = bit_errors / total_bits

    mse = float(np.mean((orig_f - dec_f) ** 2))
    snr_db = float(10 * np.log10(np.mean(orig_f**2) / mse)) if mse > 0 else float('inf')

    # Sync error: |x_drive - x_regenerated|
    sync_err = float(np.mean(np.abs(x_drive_int[-500:] - x_int[-500:])) / 65536)

    print(f"  Pearson r : {pearson_r:.6f}  {'PASS' if pearson_r>=0.95 else 'FAIL'}")
    print(f"  BER       : {ber:.6f}  {'PASS' if ber<0.01 else 'FAIL'}")
    print(f"  MSE       : {mse:.2f}")
    print(f"  SNR       : {snr_db:.2f} dB")
    print(f"  sync err  : {sync_err:.6f}")

    # ─── Save decrypted audio ────────────────────────────────────────────────
    out_dir = os.path.dirname(os.path.abspath(encrypted_wav))
    base    = os.path.splitext(os.path.basename(encrypted_wav))[0].replace('_encrypted', '')
    dec_path = os.path.join(out_dir, f"{base}_decrypted.wav")
    wavfile.write(dec_path, sr_c, decrypted)

    return {
        'sample_rate' : sr_c,
        'decrypted'   : decrypted,
        'dec_path'    : dec_path,
        'pearson_r'   : pearson_r,
        'ber'         : ber,
        'mse'         : mse,
        'snr_db'      : snr_db,
        'sync_err'    : sync_err,
    }
