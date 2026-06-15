"""
Hybrid encryptor + decryptor — Chua ⊕ Rössler stream cipher.

API mirrors python/reference/encryptor.py and decryptor.py but uses
HybridGenerator to produce the combined keystream.

Pipeline:
    audio[n] ⊕ (K_chua[n] ⊕ K_rossler[n]) = ciphertext[n]
    ciphertext[n] ⊕ (K_chua[n] ⊕ K_rossler[n]) = audio[n]    (XOR self-inverse)
"""

import os
import sys
import numpy as np
import scipy.io.wavfile as wavfile

sys.path.insert(0, os.path.dirname(__file__))
from hybrid_generator import HybridGenerator


def _load_audio_mono(path):
    sr, samples = wavfile.read(path)
    if samples.ndim == 2:
        samples = samples[:, 0]
    return sr, samples.astype(np.int16)


def encrypt_hybrid(input_wav, output_dir, chua_ics=None, rossler_ics=None,
                   rossler_role='master'):
    """
    Encrypt input_wav using the hybrid Chua⊕Rössler keystream.

    Returns dict with paths and arrays.
    """
    os.makedirs(output_dir, exist_ok=True)

    print(f"=== Hybrid encryptor ===")
    sr, plaintext = _load_audio_mono(input_wav)
    n = len(plaintext)
    print(f"  Loaded {n} samples @ {sr} Hz")

    gen  = HybridGenerator(chua_ics=chua_ics,
                            rossler_ics=rossler_ics,
                            rossler_role=rossler_role)
    data = gen.generate(n)

    plain_u   = plaintext.view(np.uint16)
    cipher_u  = np.bitwise_xor(plain_u, data['keystream'])
    ciphertext = cipher_u.view(np.int16)

    base       = os.path.splitext(os.path.basename(input_wav))[0]
    enc_path   = os.path.join(output_dir, f"hybrid_{base}_encrypted.wav")
    chua_drv   = os.path.join(output_dir, f"hybrid_{base}_chua_drive.npy")
    ross_drv   = os.path.join(output_dir, f"hybrid_{base}_rossler_drive.npy")
    ks_path    = os.path.join(output_dir, f"hybrid_{base}_keystream.npy")

    wavfile.write(enc_path, sr, ciphertext)
    np.save(chua_drv, data['chua']['x_int'])
    np.save(ross_drv, data['rossler']['x_int'])
    np.save(ks_path,  data['keystream'])

    print(f"  Saved: {os.path.basename(enc_path)}")

    return {
        'sample_rate' : sr,
        'plaintext'   : plaintext,
        'ciphertext'  : ciphertext,
        'keystream'   : data['keystream'],
        'enc_path'    : enc_path,
        'chua_drive'  : chua_drv,
        'rossler_drive': ross_drv,
        'ks_path'     : ks_path,
    }


def decrypt_hybrid(encrypted_wav, original_wav,
                   chua_drive_npy, rossler_drive_npy,
                   sync_mode='preshared',
                   chua_ics=None, rossler_ics=None, rossler_role='slave'):
    """
    Decrypt with the hybrid keystream.

    sync_mode:
        'preshared'      → both sides use same ICs, regenerate keystream
        'pecora_carroll' → receiver uses driven-subsystem regeneration
                           (Chua sync is full; Rössler sync is x-trivial)
    """
    print(f"=== Hybrid decryptor [{sync_mode}] ===")

    sr_c, ciphertext = _load_audio_mono(encrypted_wav)
    _,    original   = _load_audio_mono(original_wav)
    chua_drv         = np.load(chua_drive_npy).astype(np.int64)
    rossler_drv      = np.load(rossler_drive_npy).astype(np.int64)

    n = min(len(ciphertext), len(original), len(chua_drv), len(rossler_drv))
    ciphertext  = ciphertext[:n]
    original    = original[:n]
    chua_drv    = chua_drv[:n]
    rossler_drv = rossler_drv[:n]

    gen = HybridGenerator(chua_ics=chua_ics,
                          rossler_ics=rossler_ics,
                          rossler_role=(rossler_role if sync_mode == 'pecora_carroll' else 'master'))

    if sync_mode == 'pecora_carroll':
        data = gen.generate(n, chua_drive=chua_drv, rossler_drive=rossler_drv)
    else:
        data = gen.generate(n)

    cipher_u  = ciphertext.view(np.uint16)
    plain_u   = np.bitwise_xor(cipher_u, data['keystream'])
    decrypted = plain_u.view(np.int16)

    # ─── Metrics ─────────────────────────────────────────────────────────────
    orig_f = original.astype(np.float64)
    dec_f  = decrypted.astype(np.float64)

    pearson_r = (float(np.corrcoef(orig_f, dec_f)[0,1])
                 if orig_f.std()>1e-9 and dec_f.std()>1e-9 else 0.0)
    bits = np.unpackbits(np.bitwise_xor(
        original.view(np.uint16), decrypted.view(np.uint16)).view(np.uint8)).sum()
    ber  = bits / (len(original)*16)
    mse  = float(np.mean((orig_f-dec_f)**2))
    snr  = float(10*np.log10(np.mean(orig_f**2)/mse)) if mse>0 else float('inf')

    print(f"  Pearson r : {pearson_r:.6f}  {'PASS' if pearson_r>=0.95 else 'FAIL'}")
    print(f"  BER       : {ber:.6f}  {'PASS' if ber<0.01 else 'FAIL'}")
    print(f"  MSE       : {mse:.2f}")
    print(f"  SNR       : {snr:.2f} dB")

    out_dir  = os.path.dirname(os.path.abspath(encrypted_wav))
    base     = os.path.splitext(os.path.basename(encrypted_wav))[0].replace('_encrypted','')
    dec_path = os.path.join(out_dir, f"{base}_decrypted.wav")
    wavfile.write(dec_path, sr_c, decrypted)

    return {
        'sample_rate': sr_c,
        'decrypted'  : decrypted,
        'dec_path'   : dec_path,
        'pearson_r'  : pearson_r,
        'ber'        : ber,
        'mse'        : mse,
        'snr_db'     : snr,
    }
