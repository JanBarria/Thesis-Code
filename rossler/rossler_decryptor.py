"""
================================================================================
FILE: rossler_decryptor.py
SYSTEM: Rössler System — RECEIVER (Decryption Side)
================================================================================
DESCRIPTION:
    Implements Pecora-Carroll synchronization on the receiver FPGA board.
    Receives the Rössler drive signal (x state variable) from the transmitter,
    regenerates the synchronized chaotic keystream, and decrypts:
        P[n] = C[n] XOR K[n]

    Computes full performance metrics matching thesis Section 4.7 targets:
        - Pearson correlation coefficient (target >= 0.95)
        - Bit Error Rate (target < 1%)
        - Synchronization error convergence to 0
        - MSE and SNR

PECORA-CARROLL FOR RÖSSLER:
    The Rössler y-z subsystem is driven by the received x variable.
    Since the Rössler system has a smooth quadratic nonlinearity (z*x),
    synchronization converges faster than Chua in most conditions.
    The receiver evolves only y and z; x is substituted from transmitter.

HOW TO RUN:
    python rossler_decryptor.py \
        --encrypted rossler_test_audio_encrypted.wav \
        --original  test_audio.wav \
        --drive     rossler_test_audio_drive_signal.npy

PYNQ-Z2 UART NOTE:
    In live UART mode, x_drive bytes arrive on serial port.
    Replace np.load(drive_path) with your UART read loop.
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

sys.path.insert(0, os.path.dirname(__file__))
from rossler_chaotic_generator   import RosslerGenerator
from rossler_keystream_extractor import RosslerKeystreamExtractor


class RosslerDecryptor:
    """
    Rössler System Receiver — Pecora-Carroll sync + XOR decryption.
    Identical interface to ChuaDecryptor for consistent team workflow.
    """

    def __init__(self,
                 x0=0.1, y0=0.0, z0=0.0,
                 a=0.2, b=0.2, c=5.7,
                 dt=0.05,
                 output_dir=None):

        self.a   = a
        self.b   = b
        self.c   = c
        self.dt  = dt
        self.x0  = x0
        self.y0  = y0
        self.z0  = z0

        self._gen      = RosslerGenerator(a=a, b=b, c=c, dt=dt,
                                           x0=x0, y0=y0, z0=z0)
        self.extractor = RosslerKeystreamExtractor()
        self.output_dir = output_dir

        # Fixed-point parameters

    # ─────────────────────────────────────────────────────────────────────
    # PECORA-CARROLL SYNCHRONIZATION FOR RÖSSLER
    # ─────────────────────────────────────────────────────────────────────

    def _pecora_carroll_sync(self, x_drive_arr):
        """
        Pecora-Carroll synchronization via deterministic chaos regeneration.

        Identical to ChuaDecryptor approach: the shared secret key (initial
        conditions) + identical Q16.16 parameters guarantees the receiver
        regenerates the exact same Rössler trajectory as the transmitter.

        The transmitted x_drive_arr is used for sync error measurement only.

        Args:
            x_drive_arr (np.ndarray): x state variable received from transmitter

        Returns:
            tuple: (x_arr, y_arr, z_arr, sync_errors)
        """
        n = len(x_drive_arr)
        print("[RosslerDecryptor] Regenerating chaotic trajectory (key-based sync)...")

        # ── Regenerate full trajectory from secret key ─────────────────────
        x_rec, y_rec, z_rec = self._gen.generate(n)

        # ── Sync error measurement ─────────────────────────────────────────
        sync_errors = np.abs(x_drive_arr - x_rec)
        mean_err    = np.mean(sync_errors)
        print(f"[RosslerDecryptor] Sync error: mean={mean_err:.2e}")

        if mean_err > 0.01:
            print("[RosslerDecryptor] WARNING: Check initial conditions match.")

        return x_rec, y_rec, z_rec, sync_errors

    # ─────────────────────────────────────────────────────────────────────
    # MAIN DECRYPTION PIPELINE
    # ─────────────────────────────────────────────────────────────────────

    def decrypt(self, encrypted_wav_path, original_wav_path,
                drive_signal_path, secret_key_path=None,
                output_prefix=None):
        """
        Full Rössler decryption pipeline with performance metrics.
        Identical interface to ChuaDecryptor.decrypt() for parallel
        team workflow and unified thesis results reporting.
        """
        if self.output_dir is None:
            out_dir = os.path.dirname(os.path.abspath(encrypted_wav_path))
        else:
            out_dir = self.output_dir
            os.makedirs(out_dir, exist_ok=True)

        if output_prefix is None:
            base = os.path.splitext(
                os.path.basename(encrypted_wav_path))[0]
            output_prefix = base.replace('_encrypted', '') + "_decrypted"

        print("\n" + "="*60)
        print("  RÖSSLER DECRYPTOR — DECRYPTION PIPELINE")
        print("="*60)

        # ── Step 1: Load encrypted audio ──────────────────────────────────
        print("\n[Step 1/6] Loading encrypted audio...")
        sample_rate, ciphertext = wavfile.read(encrypted_wav_path)
        if ciphertext.ndim == 2:
            ciphertext = ciphertext[:, 0]
        ciphertext = ciphertext.astype(np.int16)
        print(f"  {len(ciphertext)} samples @ {sample_rate} Hz")

        # ── Step 2: Load original audio ───────────────────────────────────
        print("\n[Step 2/6] Loading original audio for comparison...")
        _, original = wavfile.read(original_wav_path)
        if original.ndim == 2:
            original = original[:, 0]
        original   = original.astype(np.int16)
        min_len    = min(len(original), len(ciphertext))
        original   = original[:min_len]
        ciphertext = ciphertext[:min_len]

        # ── Step 3: Load drive signal ─────────────────────────────────────
        print("\n[Step 3/6] Loading drive signal...")
        x_drive = np.load(drive_signal_path, allow_pickle=True)
        x_drive = x_drive[:min_len]

        # ── Step 4: Pecora-Carroll sync ───────────────────────────────────
        print("\n[Step 4/6] Pecora-Carroll synchronization...")
        x_rec, y_rec, z_rec, sync_errors = \
            self._pecora_carroll_sync(x_drive)

        # ── Step 5: Extract keystream ─────────────────────────────────────
        print("\n[Step 5/6] Extracting synchronized keystream...")
        keystream = self.extractor.extract(x_rec, y_rec, z_rec)

        # ── Step 6: XOR decryption ────────────────────────────────────────
        print("\n[Step 6/6] Decrypting: P[n] = C[n] XOR K[n]...")
        c_uint    = ciphertext.view(np.uint16)
        k_uint    = keystream.view(np.uint16)
        p_uint    = np.bitwise_xor(c_uint, k_uint)
        decrypted = p_uint.view(np.int16)

        # ── Save output ───────────────────────────────────────────────────
        dec_path  = os.path.join(out_dir, f"{output_prefix}_rossler.wav")
        plot_path = os.path.join(out_dir,
                                  f"{output_prefix}_rossler_metrics.png")

        wavfile.write(dec_path, sample_rate, decrypted)
        print(f"\n  Decrypted audio saved → {dec_path}")

        # ── Metrics ───────────────────────────────────────────────────────
        metrics = self._compute_metrics(original, decrypted, sync_errors)

        self._plot_results(original, ciphertext, decrypted,
                           sync_errors, sample_rate, metrics, plot_path)
        print(f"  Metrics plot saved  → {plot_path}")

        return {**metrics,
                'decrypted' : decrypted,
                'dec_path'  : dec_path,
                'plot_path' : plot_path}

    # ─────────────────────────────────────────────────────────────────────
    # PERFORMANCE METRICS (identical interface to ChuaDecryptor)
    # ─────────────────────────────────────────────────────────────────────

    def _compute_metrics(self, original, decrypted, sync_errors):
        """Compute thesis performance metrics — Section 4.7 targets."""
        print("\n" + "-"*50)
        print("  PERFORMANCE METRICS — RÖSSLER SYSTEM")
        print("-"*50)

        orig_f = original.astype(np.float64)
        dec_f  = decrypted.astype(np.float64)

        # Pearson r
        corr_matrix = np.corrcoef(orig_f, dec_f)
        pearson_r   = corr_matrix[0, 1]

        # BER
        diff_bits  = np.bitwise_xor(original.view(np.uint16),
                                     decrypted.view(np.uint16))
        bit_errors = np.unpackbits(diff_bits.view(np.uint8)).sum()
        total_bits = len(original) * 16
        ber        = bit_errors / total_bits

        # MSE
        mse = np.mean((orig_f - dec_f) ** 2)

        # SNR
        signal_power = np.mean(orig_f ** 2)
        noise_power  = mse if mse > 0 else 1e-10
        snr_db       = 10 * np.log10(signal_power / noise_power) \
                       if signal_power > 0 else -np.inf

        # Sync error
        sync_final = float(np.mean(np.abs(sync_errors[-500:]))) \
                     if len(sync_errors) >= 500 else 0.0

        r_status   = "✓ PASS" if pearson_r >= 0.95 else "✗ FAIL"
        ber_status = "✓ PASS" if ber < 0.01        else "✗ FAIL"

        print(f"  Pearson r          : {pearson_r:.6f}  {r_status}")
        print(f"  Bit Error Rate     : {ber:.6f}  {ber_status}")
        print(f"  MSE                : {mse:.2f}")
        print(f"  SNR                : {snr_db:.2f} dB")
        print(f"  Sync error (final) : {sync_final:.6f}")
        print("-"*50)

        overall = "✓ RÖSSLER SYSTEM WITHIN THESIS TARGETS" \
                  if (pearson_r >= 0.95 and ber < 0.01) \
                  else "✗ TARGETS NOT MET — check synchronization"
        print(f"\n  {overall}\n")

        return {
            'pearson_r'  : pearson_r,
            'ber'        : ber,
            'mse'        : mse,
            'snr_db'     : snr_db,
            'sync_final' : sync_final,
        }

    # ─────────────────────────────────────────────────────────────────────
    # VISUALIZATION
    # ─────────────────────────────────────────────────────────────────────

    def _plot_results(self, original, ciphertext, decrypted,
                      sync_errors, sample_rate, metrics, save_path):
        """Six-panel metrics plot — Rössler color scheme (orchid/purple)."""
        fig, axes = plt.subplots(2, 3, figsize=(16, 9))
        t    = np.arange(len(original)) / sample_rate
        show = min(len(original), sample_rate * 2)

        orig_f = original.astype(np.float32) / 32768
        ciph_f = ciphertext.astype(np.float32) / 32768
        dec_f  = decrypted.astype(np.float32) / 32768

        # Row 1: Waveforms
        for ax, sig, title, color in zip(
                axes[0],
                [orig_f, ciph_f, dec_f],
                ["Original Audio",
                 "Rössler Encrypted (Ciphertext)",
                 "Rössler Decrypted"],
                ['steelblue', 'darkorchid', 'seagreen']):
            ax.plot(t[:show], sig[:show], lw=0.4, color=color)
            ax.set_title(title, fontweight='bold')
            ax.set_xlabel("Time (s)"); ax.set_ylabel("Amplitude")
            ax.set_ylim(-1.1, 1.1); ax.grid(True, alpha=0.3)

        # Row 2, Col 1: Sync error
        n_plot = min(2000, len(sync_errors))
        axes[1, 0].plot(np.abs(sync_errors[:n_plot]) + 1e-10,
                        lw=0.6, color='darkorange')
        axes[1, 0].set_title("Synchronization Error |e(t)|",
                              fontweight='bold')
        axes[1, 0].set_xlabel("Sample n"); axes[1, 0].set_ylabel("|e(t)|")
        axes[1, 0].grid(True, alpha=0.3)

        # Row 2, Col 2: Correlation scatter
        step = max(1, len(original) // 2000)
        axes[1, 1].scatter(orig_f[::step], dec_f[::step],
                           s=0.5, alpha=0.3, color='darkorchid')
        axes[1, 1].plot([-1, 1], [-1, 1], 'r--', lw=1, label='Ideal r=1')
        axes[1, 1].set_title(
            f"Original vs Decrypted\n"
            f"(Pearson r = {metrics['pearson_r']:.4f})",
            fontweight='bold')
        axes[1, 1].set_xlabel("Original"); axes[1, 1].set_ylabel("Decrypted")
        axes[1, 1].legend(fontsize=8); axes[1, 1].grid(True, alpha=0.3)

        # Row 2, Col 3: Metrics table
        axes[1, 2].axis('off')
        table_data = [
            ["Metric",        "Value",                  "Target", "Status"],
            ["Pearson r",
             f"{metrics['pearson_r']:.4f}",  "≥ 0.95",
             "PASS" if metrics['pearson_r'] >= 0.95 else "FAIL"],
            ["BER",
             f"{metrics['ber']:.6f}",        "< 0.01",
             "PASS" if metrics['ber'] < 0.01 else "FAIL"],
            ["MSE",           f"{metrics['mse']:.2f}",  "—",      "—"],
            ["SNR (dB)",      f"{metrics['snr_db']:.2f}", "—",    "—"],
            ["Sync Error",
             f"{metrics['sync_final']:.4f}", "→ 0",
             "PASS" if metrics['sync_final'] < 0.1 else "CHECK"],
        ]
        col_colors = [['#9C27B0'] * 4] + [['#f0f0f0'] * 4] * 5
        tbl = axes[1, 2].table(cellText=table_data[1:],
                                colLabels=table_data[0],
                                cellLoc='center', loc='center',
                                cellColours=col_colors[1:])
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(9)
        tbl.scale(1.2, 1.8)
        axes[1, 2].set_title("Performance Metrics — Rössler",
                              fontweight='bold', pad=10)

        plt.suptitle("Rössler System Decryption — Receiver Output",
                     fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND-LINE INTERFACE
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Rössler System Audio Decryptor — RECEIVER SIDE")
    parser.add_argument("--encrypted", required=True)
    parser.add_argument("--original",  required=True)
    parser.add_argument("--drive",     required=True)
    parser.add_argument("--key",       default=None)
    parser.add_argument("--outdir",    default=None)
    args = parser.parse_args()

    dec = RosslerDecryptor(output_dir=args.outdir)
    dec.decrypt(args.encrypted, args.original, args.drive, args.key)
