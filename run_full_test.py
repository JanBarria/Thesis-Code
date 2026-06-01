"""
================================================================================
FILE: run_full_test.py
SYSTEM: End-to-End Test Runner — Chua + Rössler Parallel
================================================================================
DESCRIPTION:
    Runs a complete end-to-end test of BOTH the Chua and Rössler encryption/
    decryption pipelines using a synthetic test audio file.

    Use this to verify both systems work on your PYNQ-Z2 board before
    loading real audio files.

HOW TO RUN:
    python run_full_test.py

    Or with a real audio file:
        python run_full_test.py --wav path/to/your_audio.wav

EXPECTED OUTPUT:
    outputs/
        test_audio.wav                         — synthetic test signal
        chua/
            chua_test_audio_encrypted.wav
            chua_test_audio_secret_key.npy
            chua_test_audio_drive_signal.npy
            chua_test_audio_encrypt_plot.png
            test_audio_decrypted_chua.wav
            test_audio_decrypted_chua_metrics.png
        rossler/
            rossler_test_audio_encrypted.wav
            (same structure as chua/)
        comparison_summary.png                 — side-by-side system comparison
================================================================================
"""

import numpy as np
import scipy.io.wavfile as wavfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import sys
import argparse

# ── Path setup ────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CHUA_DIR    = os.path.join(BASE_DIR, "chua")
ROSSLER_DIR = os.path.join(BASE_DIR, "rossler")
OUT_DIR     = os.path.join(BASE_DIR, "outputs")

sys.path.insert(0, CHUA_DIR)
sys.path.insert(0, ROSSLER_DIR)

from chua_encryptor    import ChuaEncryptor
from chua_decryptor    import ChuaDecryptor
from rossler_encryptor import RosslerEncryptor
from rossler_decryptor import RosslerDecryptor


# ─────────────────────────────────────────────────────────────────────────────
# SYNTHETIC TEST AUDIO GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def generate_test_audio(output_path, duration=3.0, sample_rate=8000):
    """
    Generate a synthetic mono 16-bit PCM .wav test file.
    Uses a mix of sine waves to simulate speech-like content.

    Args:
        output_path  : Where to save the .wav file
        duration     : Duration in seconds (default 3s)
        sample_rate  : Sample rate in Hz (default 8000 for IoT-like usage)

    Returns:
        str: Path to the generated file
    """
    t       = np.linspace(0, duration, int(sample_rate * duration),
                          endpoint=False)
    # Mix of fundamental + harmonics to simulate speech
    signal  = (0.4  * np.sin(2 * np.pi * 440  * t) +   # A4
               0.3  * np.sin(2 * np.pi * 880  * t) +   # A5
               0.2  * np.sin(2 * np.pi * 1320 * t) +   # E6
               0.1  * np.sin(2 * np.pi * 261  * t))    # C4
    # Add slight envelope
    envelope = np.exp(-0.3 * t) * np.sin(np.pi * t / duration) ** 0.5
    signal   = signal * envelope

    # Normalize and convert to int16
    signal  /= np.max(np.abs(signal)) + 1e-8
    signal   = (signal * 28000).astype(np.int16)   # ~85% of int16 range

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    wavfile.write(output_path, sample_rate, signal)
    print(f"[TestGen] Synthetic audio created: {output_path}")
    print(f"          {len(signal)} samples @ {sample_rate} Hz "
          f"({duration:.1f}s)")
    return output_path


# ─────────────────────────────────────────────────────────────────────────────
# COMPARISON SUMMARY PLOT
# ─────────────────────────────────────────────────────────────────────────────

def plot_comparison_summary(chua_metrics, rossler_metrics, save_path):
    """
    Generate a side-by-side comparison of Chua vs Rössler performance.
    This plot is suitable for direct inclusion in thesis Chapter 5/6 results.
    """
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    systems  = ['Chua Circuit', 'Rössler System']
    colors   = ['steelblue', 'darkorchid']

    # ── Bar 1: Pearson r ──────────────────────────────────────────────────
    r_vals = [chua_metrics['pearson_r'], rossler_metrics['pearson_r']]
    bars   = axes[0].bar(systems, r_vals, color=colors, width=0.4,
                          edgecolor='white')
    axes[0].axhline(y=0.95, color='red', linestyle='--',
                    linewidth=1.5, label='Thesis target (0.95)')
    axes[0].set_title("Pearson Correlation Coefficient\n(target ≥ 0.95)",
                      fontweight='bold')
    axes[0].set_ylabel("r value")
    axes[0].set_ylim(0, 1.1)
    axes[0].legend(fontsize=8)
    axes[0].grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars, r_vals):
        axes[0].text(bar.get_x() + bar.get_width()/2,
                     bar.get_height() + 0.01,
                     f"{val:.4f}", ha='center', va='bottom', fontsize=9)

    # ── Bar 2: BER ────────────────────────────────────────────────────────
    ber_vals = [chua_metrics['ber'], rossler_metrics['ber']]
    bars2    = axes[1].bar(systems, ber_vals, color=colors, width=0.4,
                            edgecolor='white')
    axes[1].axhline(y=0.01, color='red', linestyle='--',
                    linewidth=1.5, label='Thesis target (1%)')
    axes[1].set_title("Bit Error Rate\n(target < 1%)", fontweight='bold')
    axes[1].set_ylabel("BER")
    axes[1].legend(fontsize=8)
    axes[1].grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars2, ber_vals):
        axes[1].text(bar.get_x() + bar.get_width()/2,
                     bar.get_height() + 0.0002,
                     f"{val:.4f}", ha='center', va='bottom', fontsize=9)

    # ── Table: Full metrics comparison ───────────────────────────────────
    axes[2].axis('off')
    metrics_labels = ['Pearson r', 'BER', 'MSE', 'SNR (dB)',
                      'Sync Error', 'r Target Met', 'BER Target Met']

    def fmt(v):
        if isinstance(v, float):
            return f"{v:.4f}"
        return str(v)

    chua_vals = [
        fmt(chua_metrics['pearson_r']),
        fmt(chua_metrics['ber']),
        fmt(chua_metrics['mse']),
        fmt(chua_metrics['snr_db']),
        fmt(chua_metrics['sync_final']),
        "✓ YES" if chua_metrics['pearson_r'] >= 0.95 else "✗ NO",
        "✓ YES" if chua_metrics['ber']       <  0.01 else "✗ NO",
    ]
    rossler_vals = [
        fmt(rossler_metrics['pearson_r']),
        fmt(rossler_metrics['ber']),
        fmt(rossler_metrics['mse']),
        fmt(rossler_metrics['snr_db']),
        fmt(rossler_metrics['sync_final']),
        "✓ YES" if rossler_metrics['pearson_r'] >= 0.95 else "✗ NO",
        "✓ YES" if rossler_metrics['ber']       <  0.01 else "✗ NO",
    ]

    table_data = [[lbl, c, r] for lbl, c, r in
                  zip(metrics_labels, chua_vals, rossler_vals)]
    col_colors = [['#E3F2FD', '#BBDEFB', '#CE93D8']] * len(table_data)

    tbl = axes[2].table(
        cellText   = table_data,
        colLabels  = ['Metric', 'Chua Circuit', 'Rössler System'],
        cellLoc    = 'center', loc='center',
        cellColours= col_colors)
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1.2, 1.8)
    axes[2].set_title("System Performance Comparison\n(Thesis SO6 Evaluation)",
                      fontweight='bold', pad=15)

    plt.suptitle("Chaos-Based Secure Communication — System Comparison\n"
                 "Chua Circuit vs Rössler System | PYNQ-Z2 FPGA",
                 fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\n[Summary] Comparison plot saved → {save_path}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN TEST RUNNER
# ─────────────────────────────────────────────────────────────────────────────

def main(wav_path=None):
    os.makedirs(OUT_DIR, exist_ok=True)
    chua_out    = os.path.join(OUT_DIR, "chua")
    rossler_out = os.path.join(OUT_DIR, "rossler")
    os.makedirs(chua_out,    exist_ok=True)
    os.makedirs(rossler_out, exist_ok=True)

    # ── Generate or use provided audio ───────────────────────────────────
    if wav_path is None:
        test_wav = os.path.join(OUT_DIR, "test_audio.wav")
        generate_test_audio(test_wav, duration=3.0, sample_rate=8000)
    else:
        test_wav = wav_path
        print(f"[Main] Using provided audio: {test_wav}")

    # ─────────────────────────────────────────────────────────────────────
    # CHUA PIPELINE (Barria & Jusay)
    # ─────────────────────────────────────────────────────────────────────
    print("\n" + "█"*60)
    print("  PART 1: CHUA CIRCUIT PIPELINE")
    print("█"*60)

    chua_enc = ChuaEncryptor(x0=0.1, y0=0.0, z0=0.0, output_dir=chua_out)
    chua_result = chua_enc.encrypt(test_wav)

    chua_dec = ChuaDecryptor(x0=0.1, y0=0.0, z0=0.0, output_dir=chua_out)
    chua_metrics = chua_dec.decrypt(
        encrypted_wav_path = chua_result['enc_path'],
        original_wav_path  = test_wav,
        drive_signal_path  = chua_result['drive_path'],
        secret_key_path    = chua_result['key_path']
    )

    # ─────────────────────────────────────────────────────────────────────
    # RÖSSLER PIPELINE (Cortes & Abalos)
    # ─────────────────────────────────────────────────────────────────────
    print("\n" + "█"*60)
    print("  PART 2: RÖSSLER SYSTEM PIPELINE")
    print("█"*60)

    ross_enc = RosslerEncryptor(x0=1.0, y0=1.0, z0=1.0, output_dir=rossler_out)
    ross_result = ross_enc.encrypt(test_wav)

    ross_dec = RosslerDecryptor(x0=1.0, y0=1.0, z0=1.0, output_dir=rossler_out)
    ross_metrics = ross_dec.decrypt(
        encrypted_wav_path = ross_result['enc_path'],
        original_wav_path  = test_wav,
        drive_signal_path  = ross_result['drive_path'],
        secret_key_path    = ross_result['key_path']
    )

    # ─────────────────────────────────────────────────────────────────────
    # COMPARISON SUMMARY
    # ─────────────────────────────────────────────────────────────────────
    print("\n" + "█"*60)
    print("  PART 3: SYSTEM COMPARISON")
    print("█"*60)

    summary_path = os.path.join(OUT_DIR, "comparison_summary.png")
    plot_comparison_summary(chua_metrics, ross_metrics, summary_path)

    # ── Final report ──────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("  FINAL TEST REPORT")
    print("="*60)
    print(f"  {'System':<20} {'Pearson r':>12} {'BER':>10} {'Pass?':>8}")
    print(f"  {'-'*52}")

    for name, m in [("Chua Circuit", chua_metrics),
                    ("Rössler System", ross_metrics)]:
        passed = (m['pearson_r'] >= 0.95 and m['ber'] < 0.01)
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name:<20} {m['pearson_r']:>12.4f} "
              f"{m['ber']:>10.6f} {status:>8}")

    print(f"\n  All outputs saved to: {OUT_DIR}")
    print("="*60)

    return chua_metrics, ross_metrics


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="End-to-end test for Chua + Rössler encryption systems")
    parser.add_argument("--wav", default=None,
                        help="Path to real .wav file (optional). "
                             "If not provided, synthetic audio is generated.")
    args = parser.parse_args()
    main(wav_path=args.wav)
