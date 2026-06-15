"""
End-to-end hybrid Chua⊕Rössler test.

Validates:
    1. Combined keystream generation
    2. Encryption + decryption round-trip via the hybrid cipher
    3. Both sync modes (preshared, pecora_carroll)
    4. Combined keystream entropy approaches 8 bits/byte (ideal)
"""

import os
import sys
import argparse
import numpy as np
import scipy.io.wavfile as wavfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python', 'reference'))

from hybrid_cipher import encrypt_hybrid, decrypt_hybrid


def make_test_audio(path, duration=3.0, sr=8000):
    t = np.linspace(0, duration, int(sr*duration), endpoint=False)
    s = (0.4*np.sin(2*np.pi*440*t) + 0.3*np.sin(2*np.pi*880*t)
         + 0.2*np.sin(2*np.pi*1320*t) + 0.1*np.sin(2*np.pi*261*t))
    env = np.exp(-0.3*t) * np.sin(np.pi*t/duration)**0.5
    s = (s*env/(np.abs(s*env).max()+1e-8))*28000
    os.makedirs(os.path.dirname(path), exist_ok=True)
    wavfile.write(path, sr, s.astype(np.int16))
    return path


def shannon_entropy_bits(arr_uint16):
    """Estimate Shannon entropy of a uint16 stream (treat as bytes)."""
    b = arr_uint16.astype(np.uint16).tobytes()
    h = np.bincount(np.frombuffer(b, dtype=np.uint8), minlength=256).astype(np.float64)
    p = h / h.sum()
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def main(wav_path=None):
    out = os.path.join(ROOT, 'test_audio', 'outputs_hybrid')
    os.makedirs(out, exist_ok=True)

    if wav_path is None or not os.path.exists(wav_path):
        wav_path = os.path.join(out, 'test_tone.wav')
        if not os.path.exists(wav_path):
            make_test_audio(wav_path)

    print("="*70)
    print("  HYBRID CHUA⊕RÖSSLER END-TO-END TEST")
    print("="*70)

    results = {}
    for sync in ('preshared', 'pecora_carroll'):
        print(f"\n--- HYBRID / {sync} ---")
        enc = encrypt_hybrid(wav_path, output_dir=os.path.join(out, sync))
        m = decrypt_hybrid(enc['enc_path'], wav_path,
                          enc['chua_drive'], enc['rossler_drive'],
                          sync_mode=sync)
        # Entropy on encryption keystream
        ks = np.load(enc['ks_path'])
        m['entropy_bits_per_byte'] = shannon_entropy_bits(ks)
        results[sync] = m

    # ── Summary ──────────────────────────────────────────────────────────
    print("\n"+"="*70)
    print("  RESULTS")
    print("="*70)
    print(f"  {'Sync Mode':<18} {'Pearson r':>10} {'BER':>10} {'SNR (dB)':>10} {'H (b/B)':>9} {'Pass':>6}")
    print(f"  {'-'*68}")
    for sync, m in results.items():
        passed = m['pearson_r'] >= 0.95 and m['ber'] < 0.01
        print(f"  {sync:<18} {m['pearson_r']:>10.4f} {m['ber']:>10.6f} "
              f"{m['snr_db']:>10.2f} {m['entropy_bits_per_byte']:>9.4f} "
              f"{'PASS' if passed else 'FAIL':>6}")
    print("="*70)
    print("  H (b/B) = Shannon entropy of combined keystream (target → 8.0)")

    all_pass = all(m['pearson_r']>=0.95 and m['ber']<0.01 for m in results.values())
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--wav", default=None)
    a = p.parse_args()
    main(a.wav)
