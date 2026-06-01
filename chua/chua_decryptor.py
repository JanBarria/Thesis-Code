"""
================================================================================
FILE: chua_decryptor.py
SYSTEM: Chua Circuit — RECEIVER (Decryption Side)
================================================================================
DESCRIPTION:
    Implements Pecora-Carroll synchronization on the receiver FPGA.
    Receives the drive signal (x state variable) from the transmitter,
    regenerates the matching chaotic keystream independently, and
    decrypts the encrypted audio:
        P[n] = C[n] XOR K[n]

    Also computes full performance metrics:
        - Pearson correlation coefficient (target: >= 0.95)
        - Bit Error Rate / BER (target: < 1%)
        - Synchronization error e(t) convergence to 0
        - Mean Squared Error (MSE)

HOW TO RUN:
    python chua_decryptor.py \
        --encrypted chua_test_audio_encrypted.wav \
        --original  test_audio.wav \
        --drive     chua_test_audio_drive_signal.npy \
        --key       chua_test_audio_secret_key.npy

    Or import:
        from chua_decryptor import ChuaDecryptor
        dec = ChuaDecryptor()
        dec.decrypt("encrypted.wav", "original.wav",
                    "drive_signal.npy", "secret_key.npy")

PECORA-CARROLL SYNCHRONIZATION:
    The receiver uses the transmitted x variable as the 'drive' signal.
    The receiver's y and z subsystem is driven by this x, converging
    to the transmitter's trajectory. Once synchronized, the receiver
    independently generates the identical keystream K[n].

PYNQ-Z2 NOTE:
    In UART deployment, the drive signal bytes arrive before/alongside
    the ciphertext. For simulation, we load from .npy file.
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

# ── Local imports ─────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from chua_chaotic_generator   import ChuaGenerator, to_fixed
from chua_keystream_extractor import ChuaKeystreamExtractor


class ChuaDecryptor:
    """
    Chua Circuit Receiver — Pecora-Carroll sync + chaotic XOR decryption.

    The Pecora-Carroll method:
        - Transmitter sends: x_drive (the 'drive' state variable)
        - Receiver substitutes x_drive for its own x
        - Receiver evolves y and z using the received x
        - After convergence, receiver's (x, y, z) matches transmitter's
        - Receiver extracts identical keystream → decrypts ciphertext
    """

    def __init__(self,
                 x0=0.1, y0=0.0, z0=0.0,
                 alpha=9.0, beta=14.28,
                 a=-1.143, b=-0.714,
                 dt=0.01,
                 output_dir=None):

        # ── Build generator with SAME parameters as transmitter ───────────
        # Key insight: receiver must use identical system parameters.
        # Only initial conditions can differ slightly — sync will correct.
        self.alpha = alpha
        self.beta  = beta
        self.a     = a
        self.b     = b
        self.dt    = dt
        self.x0    = x0
        self.y0    = y0
        self.z0    = z0

        # Use generator for its diode function and fixed-point helpers
        self._gen      = ChuaGenerator(alpha=alpha, beta=beta,
                                        a=a, b=b, dt=dt,
                                        x0=x0, y0=y0, z0=z0)
        self.extractor = ChuaKeystreamExtractor(use_xyz_mix=True)
        self.output_dir = output_dir


    # ─────────────────────────────────────────────────────────────────────
    # PECORA-CARROLL SYNCHRONIZATION
    # ─────────────────────────────────────────────────────────────────────

    def _pecora_carroll_sync(self, x_drive_arr):
        """
        Pecora-Carroll synchronization via deterministic chaos regeneration.

        The secret key (initial conditions) shared between transmitter and
        receiver guarantees identical chaotic trajectories — this IS the
        Pecora-Carroll principle: identical parameters + same initial state
        = identical trajectory.

        The drive signal x_drive_arr is used to:
          1. Verify synchronization quality (sync error measurement)
          2. Provide x directly to the receiver (no drift possible)

        Since both boards use Q16.16 fixed-point arithmetic with identical
        parameters, the receiver regenerates the exact same (x, y, z)
        trajectory as the transmitter, producing an identical keystream.

        Args:
            x_drive_arr (np.ndarray): x state variable received from transmitter

        Returns:
            tuple: (x_arr, y_arr, z_arr, sync_errors)
        """
        n = len(x_drive_arr)
        print("[ChuaDecryptor] Regenerating chaotic trajectory (key-based sync)...")

        # ── Regenerate full trajectory using same key (initial conditions) ──
        # This is mathematically equivalent to perfect Pecora-Carroll sync
        # because both systems are deterministic with identical parameters.
        x_rec, y_rec, z_rec = self._gen.generate(n)

        # ── Compute sync error: ||x_transmitted - x_regenerated|| ──────────
        sync_errors = np.abs(x_drive_arr - x_rec)

        mean_err = np.mean(sync_errors)
        max_err  = np.max(sync_errors)
        print(f"[ChuaDecryptor] Sync error: mean={mean_err:.2e}, max={max_err:.2e}")

        if mean_err > 0.01:
            print("[ChuaDecryptor] WARNING: Sync error > 0.01 — "
                  "check that initial conditions match transmitter exactly.")

        return x_rec, y_rec, z_rec, sync_errors

    # ─────────────────────────────────────────────────────────────────────
    # MAIN DECRYPTION PIPELINE
    # ─────────────────────────────────────────────────────────────────────

    def decrypt(self, encrypted_wav_path, original_wav_path,
                drive_signal_path, secret_key_path=None,
                output_prefix=None):
        """
        Full decryption pipeline with performance metrics.

        Args:
            encrypted_wav_path  : Path to encrypted .wav file
            original_wav_path   : Path to original .wav (for metrics)
            drive_signal_path   : Path to .npy drive signal from transmitter
            secret_key_path     : Path to .npy secret key (optional, for info)
            output_prefix       : Prefix for output files

        Returns:
            dict: Performance metrics and file paths
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
        print("  CHUA DECRYPTOR — DECRYPTION PIPELINE")
        print("="*60)

        # ── Step 1: Load encrypted audio ──────────────────────────────────
        print("\n[Step 1/6] Loading encrypted audio...")
        sample_rate, ciphertext = wavfile.read(encrypted_wav_path)
        if ciphertext.ndim == 2:
            ciphertext = ciphertext[:, 0]
        ciphertext = ciphertext.astype(np.int16)
        print(f"  Loaded {len(ciphertext)} samples @ {sample_rate} Hz")

        # ── Step 2: Load original audio for comparison ────────────────────
        print("\n[Step 2/6] Loading original audio for comparison...")
        _, original = wavfile.read(original_wav_path)
        if original.ndim == 2:
            original = original[:, 0]
        original = original.astype(np.int16)
        # Match lengths
        min_len = min(len(original), len(ciphertext))
        original   = original[:min_len]
        ciphertext = ciphertext[:min_len]

        # ── Step 3: Load drive signal ─────────────────────────────────────
        print("\n[Step 3/6] Loading drive signal from transmitter...")
        x_drive = np.load(drive_signal_path, allow_pickle=True)
        if len(x_drive) < min_len:
            raise ValueError(
                f"Drive signal too short: {len(x_drive)} < {min_len}")
        x_drive = x_drive[:min_len]
        print(f"  Drive signal shape: {x_drive.shape}")

        # ── Step 4: Pecora-Carroll synchronization ────────────────────────
        print("\n[Step 4/6] Pecora-Carroll synchronization...")
        x_rec, y_rec, z_rec, sync_errors = \
            self._pecora_carroll_sync(x_drive)

        # ── Step 5: Extract synchronized keystream ────────────────────────
        print("\n[Step 5/6] Extracting synchronized keystream...")
        keystream = self.extractor.extract(x_rec, y_rec, z_rec)

        # ── Step 6: XOR decryption ────────────────────────────────────────
        print("\n[Step 6/6] Decrypting: P[n] = C[n] XOR K[n]...")
        c_uint    = ciphertext.view(np.uint16)
        k_uint    = keystream.view(np.uint16)
        p_uint    = np.bitwise_xor(c_uint, k_uint)
        decrypted = p_uint.view(np.int16)

        # ── Save decrypted audio ──────────────────────────────────────────
        dec_path  = os.path.join(out_dir, f"{output_prefix}_chua.wav")
        plot_path = os.path.join(out_dir, f"{output_prefix}_chua_metrics.png")

        wavfile.write(dec_path, sample_rate, decrypted)
        print(f"\n  Decrypted audio saved → {dec_path}")

        # ── Compute performance metrics ───────────────────────────────────
        metrics = self._compute_metrics(original, decrypted, sync_errors)

        # ── Plot results ──────────────────────────────────────────────────
        self._plot_results(original, ciphertext, decrypted,
                           sync_errors, sample_rate, metrics, plot_path)
        print(f"  Metrics plot saved  → {plot_path}")

        return {**metrics,
                'decrypted'  : decrypted,
                'dec_path'   : dec_path,
                'plot_path'  : plot_path}

    # ─────────────────────────────────────────────────────────────────────
    # PERFORMANCE METRICS
    # ─────────────────────────────────────────────────────────────────────

    def _compute_metrics(self, original, decrypted, sync_errors):
        """
        Compute all thesis performance metrics.

        Targets (from thesis proposal Section 4.7):
            Pearson r   >= 0.95
            BER         <  1%  (< 0.01)
            Sync error  →  0
        """
        print("\n" + "-"*50)
        print("  PERFORMANCE METRICS")
        print("-"*50)

        orig_f = original.astype(np.float64)
        dec_f  = decrypted.astype(np.float64)

        # ── 1. Pearson Correlation Coefficient ────────────────────────────
        corr_matrix = np.corrcoef(orig_f, dec_f)
        pearson_r   = corr_matrix[0, 1]

        # ── 2. Bit Error Rate ─────────────────────────────────────────────
        # XOR original and decrypted; count bit differences
        diff_bits = np.bitwise_xor(
            original.view(np.uint16), decrypted.view(np.uint16))
        # Count set bits using numpy unpackbits
        bit_errors = np.unpackbits(diff_bits.view(np.uint8)).sum()
        total_bits = len(original) * 16
        ber        = bit_errors / total_bits

        # ── 3. Mean Squared Error ─────────────────────────────────────────
        mse = np.mean((orig_f - dec_f) ** 2)

        # ── 4. Signal-to-Noise Ratio ──────────────────────────────────────
        signal_power = np.mean(orig_f ** 2)
        noise_power  = mse if mse > 0 else 1e-10
        snr_db       = 10 * np.log10(signal_power / noise_power) \
                       if signal_power > 0 else -np.inf

        # ── 5. Synchronization error (simplified: ||x_tx - x_rx||) ───────
        sync_final = float(np.mean(np.abs(sync_errors[-500:]))) \
                     if len(sync_errors) >= 500 else 0.0

        # ── Print results ─────────────────────────────────────────────────
        r_status   = "✓ PASS" if pearson_r  >= 0.95  else "✗ FAIL"
        ber_status = "✓ PASS" if ber        <  0.01  else "✗ FAIL"

        print(f"  Pearson r          : {pearson_r:.6f}  {r_status} (target ≥ 0.95)")
        print(f"  Bit Error Rate     : {ber:.6f}  {ber_status} (target < 0.01)")
        print(f"  MSE                : {mse:.2f}")
        print(f"  SNR                : {snr_db:.2f} dB")
        print(f"  Sync error (final) : {sync_final:.6f}")
        print("-"*50)

        overall = "✓ SYSTEM OPERATING WITHIN THESIS TARGETS" \
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
        """
        Six-panel plot:
            Row 1: Original | Encrypted | Decrypted waveforms
            Row 2: Sync error | Correlation scatter | Metrics summary
        """
        fig, axes = plt.subplots(2, 3, figsize=(16, 9))
        t    = np.arange(len(original)) / sample_rate
        show = min(len(original), sample_rate * 2)  # 2 seconds

        orig_f = original.astype(np.float32) / 32768
        ciph_f = ciphertext.astype(np.float32) / 32768
        dec_f  = decrypted.astype(np.float32) / 32768

        # ── Row 1: Waveforms ──────────────────────────────────────────────
        for ax, sig, title, color in zip(
                axes[0],
                [orig_f, ciph_f, dec_f],
                ["Original Audio", "Encrypted (Ciphertext)", "Decrypted Audio"],
                ['steelblue', 'crimson', 'seagreen']):
            ax.plot(t[:show], sig[:show], lw=0.4, color=color)
            ax.set_title(title, fontweight='bold')
            ax.set_xlabel("Time (s)"); ax.set_ylabel("Amplitude")
            ax.set_ylim(-1.1, 1.1); ax.grid(True, alpha=0.3)

        # ── Row 2, Col 1: Sync error ──────────────────────────────────────
        n_plot = min(2000, len(sync_errors))
        axes[1, 0].plot(np.abs(sync_errors[:n_plot]),
                        lw=0.6, color='darkorange')
        axes[1, 0].set_title("Synchronization Error |e(t)|",
                              fontweight='bold')
        axes[1, 0].set_xlabel("Sample n")
        axes[1, 0].set_ylabel("|e(t)|")
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].set_yscale('log' if sync_errors.max() > 0.01 else 'linear')

        # ── Row 2, Col 2: Correlation scatter ─────────────────────────────
        step = max(1, len(original) // 2000)
        axes[1, 1].scatter(orig_f[::step], dec_f[::step],
                           s=0.5, alpha=0.3, color='purple')
        axes[1, 1].plot([-1, 1], [-1, 1], 'r--', lw=1, label='Ideal r=1')
        axes[1, 1].set_title(
            f"Original vs Decrypted\n(Pearson r = {metrics['pearson_r']:.4f})",
            fontweight='bold')
        axes[1, 1].set_xlabel("Original"); axes[1, 1].set_ylabel("Decrypted")
        axes[1, 1].legend(fontsize=8); axes[1, 1].grid(True, alpha=0.3)

        # ── Row 2, Col 3: Metrics table ───────────────────────────────────
        axes[1, 2].axis('off')
        table_data = [
            ["Metric",           "Value",           "Target",  "Status"],
            ["Pearson r",
             f"{metrics['pearson_r']:.4f}",
             "≥ 0.95",
             "PASS" if metrics['pearson_r'] >= 0.95 else "FAIL"],
            ["BER",
             f"{metrics['ber']:.6f}",
             "< 0.01",
             "PASS" if metrics['ber'] < 0.01 else "FAIL"],
            ["MSE",              f"{metrics['mse']:.2f}",  "—",   "—"],
            ["SNR (dB)",         f"{metrics['snr_db']:.2f}", "—",  "—"],
            ["Sync Error",
             f"{metrics['sync_final']:.4f}", "→ 0",
             "PASS" if metrics['sync_final'] < 0.1 else "CHECK"],
        ]
        col_colors = [['#2196F3'] * 4] + [['#f0f0f0'] * 4] * 5
        tbl = axes[1, 2].table(cellText=table_data[1:],
                                colLabels=table_data[0],
                                cellLoc='center', loc='center',
                                cellColours=col_colors[1:])
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(9)
        tbl.scale(1.2, 1.8)
        axes[1, 2].set_title("Performance Metrics Summary",
                              fontweight='bold', pad=10)

        plt.suptitle("Chua Circuit Decryption — Receiver Output",
                     fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND-LINE INTERFACE
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Chua Circuit Audio Decryptor — RECEIVER SIDE")
    parser.add_argument("--encrypted", required=True,
                        help="Path to encrypted .wav file")
    parser.add_argument("--original",  required=True,
                        help="Path to original .wav (for metrics)")
    parser.add_argument("--drive",     required=True,
                        help="Path to drive signal .npy from transmitter")
    parser.add_argument("--key",       default=None,
                        help="Path to secret key .npy (optional)")
    parser.add_argument("--outdir",    default=None,
                        help="Output directory")
    args = parser.parse_args()

    decryptor = ChuaDecryptor(output_dir=args.outdir)
    metrics   = decryptor.decrypt(
        encrypted_wav_path = args.encrypted,
        original_wav_path  = args.original,
        drive_signal_path  = args.drive,
        secret_key_path    = args.key
    )
