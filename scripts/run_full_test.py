"""
End-to-end reference test: Chua + Rössler, both sync modes.

Runs the VHDL-bit-exact Python reference against a test audio file and
verifies that:
    1. Both systems produce chaos (non-collapsed attractor)
    2. Preshared-key sync decrypts correctly (Pearson r ≈ 1.0)
    3. Pecora-Carroll true subsystem-drive sync also decrypts correctly

Usage:
    python3 scripts/run_full_test.py
    python3 scripts/run_full_test.py --wav my_audio.wav
"""

import os
import sys
import argparse
import numpy as np
import scipy.io.wavfile as wavfile

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python', 'reference'))

from encryptor import encrypt
from decryptor import decrypt


def make_test_audio(path, duration=3.0, sr=8000):
    """Generate a synthetic test tone."""
    t = np.linspace(0, duration, int(sr*duration), endpoint=False)
    s = (0.4*np.sin(2*np.pi*440*t) + 0.3*np.sin(2*np.pi*880*t)
         + 0.2*np.sin(2*np.pi*1320*t) + 0.1*np.sin(2*np.pi*261*t))
    env = np.exp(-0.3*t) * np.sin(np.pi*t/duration)**0.5
    s = (s*env / (np.abs(s*env).max() + 1e-8)) * 28000
    os.makedirs(os.path.dirname(path), exist_ok=True)
    wavfile.write(path, sr, s.astype(np.int16))
    return path


def run_one(system, wav_path, out_dir, sync_mode):
    """Run one full encrypt+decrypt cycle and return metrics."""
    enc = encrypt(wav_path, system=system, output_dir=out_dir)

    # For Rössler PC mode, slave starts with deliberately different ICs
    dec_kwargs = {}
    if system == 'rossler' and sync_mode == 'pecora_carroll':
        # Slave IC defaults (1.0, 0.5, 1.5) come from RosslerGenerator(role='slave')
        dec_kwargs['role'] = 'slave'

    m = decrypt(enc['enc_path'], wav_path, enc['drive_path'],
                system=system, sync_mode=sync_mode, **dec_kwargs)
    return m


def main(wav_path=None):
    out = os.path.join(ROOT, 'test_audio', 'outputs')
    os.makedirs(out, exist_ok=True)

    if wav_path is None or not os.path.exists(wav_path):
        wav_path = os.path.join(out, 'test_tone.wav')
        if not os.path.exists(wav_path):
            print(f"Generating synthetic test audio at {wav_path}")
            make_test_audio(wav_path)

    print("\n" + "="*70)
    print("  END-TO-END REFERENCE TEST")
    print("="*70)

    results = {}
    for system in ('chua', 'rossler'):
        for sync in ('preshared', 'pecora_carroll'):
            print(f"\n--- {system.upper()} / {sync} ---")
            r = run_one(system, wav_path, os.path.join(out, system, sync), sync)
            results[(system, sync)] = r

    # ─── Summary table ───────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("  RESULTS SUMMARY")
    print("="*70)
    print(f"  {'System':<10} {'Sync Mode':<18} {'Pearson r':>10} {'BER':>10} {'SNR (dB)':>10} {'Pass':>6}")
    print(f"  {'-'*68}")
    for (system, sync), m in results.items():
        passed = (m['pearson_r'] >= 0.95 and m['ber'] < 0.01)
        status = "PASS" if passed else "FAIL"
        print(f"  {system:<10} {sync:<18} {m['pearson_r']:>10.4f} "
              f"{m['ber']:>10.6f} {m['snr_db']:>10.2f} {status:>6}")
    print("="*70)

    # Return code: 0 if all pass
    all_pass = all((m['pearson_r'] >= 0.95 and m['ber'] < 0.01)
                   for m in results.values())
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--wav", default=None, help="Optional input .wav file")
    args = p.parse_args()
    main(args.wav)
