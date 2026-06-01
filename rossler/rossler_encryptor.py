"""
================================================================================
FILE: rossler_encryptor.py
SYSTEM: Rössler System — TRANSMITTER (Encryption Side)
================================================================================
DESCRIPTION:
    Loads a mono 16-bit PCM .wav audio file, generates a Rössler chaotic
    keystream via phase-space projection, and encrypts using bitwise XOR:
        C[n] = P[n] XOR K[n]

    Saves encrypted audio, the secret key (initial conditions), and the
    drive signal (x state variable) for Pecora-Carroll synchronization.

HOW TO RUN:
    python rossler_encryptor.py --input test_audio.wav

    Or import:
        from rossler_encryptor import RosslerEncryptor
        enc = RosslerEncryptor()
        enc.encrypt("test_audio.wav")

EXPECTED OUTPUT:
    - rossler_<name>_encrypted.wav     — encrypted audio
    - rossler_<name>_secret_key.npy    — initial conditions
    - rossler_<name>_drive_signal.npy  — x variable for receiver sync
    - rossler_<name>_encrypt_plot.png  — waveform + spectrogram comparison

NOTE FOR TEAM (Cortes & Abalos):
    This file follows the IDENTICAL structure as chua_encryptor.py.
    Both can be run in parallel on separate PYNQ-Z2 boards without conflict.
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


class RosslerEncryptor:
    """
    Rössler System Transmitter — encrypts .wav using chaotic XOR.
    Identical interface to ChuaEncryptor for parallel team workflow.
    """

    def __init__(self,
                 x0=1.0, y0=1.0, z0=1.0,
                 a=0.2, b=0.2, c=5.7,
                 dt=1310/65536,
                 output_dir=None):

        self.generator  = RosslerGenerator(a=a, b=b, c=c, dt=dt,
                                            x0=x0, y0=y0, z0=z0)
        self.extractor  = RosslerKeystreamExtractor()
        self.output_dir = output_dir

    # ─────────────────────────────────────────────────────────────────────
    # AUDIO LOADING
    # ─────────────────────────────────────────────────────────────────────

    def _load_audio(self, filepath):
        """Load mono 16-bit PCM .wav — identical to Chua encryptor."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Audio file not found: {filepath}")

        sample_rate, samples = wavfile.read(filepath)

        if samples.ndim == 2:
            print("[RosslerEncryptor] Stereo → mono downmix")
            samples = samples.mean(axis=1).astype(np.int16)

        if samples.dtype != np.int16:
            samples = samples.astype(np.int16)

        print(f"[RosslerEncryptor] Loaded: {filepath}")
        print(f"  Sample rate : {sample_rate} Hz")
        print(f"  Samples     : {len(samples)}")
        print(f"  Duration    : {len(samples)/sample_rate:.2f} seconds")

        return sample_rate, samples

    # ─────────────────────────────────────────────────────────────────────
    # ENCRYPTION PIPELINE
    # ─────────────────────────────────────────────────────────────────────

    def encrypt(self, input_wav_path, output_prefix=None):
        """
        Full Rössler encryption pipeline.
        Identical return structure to ChuaEncryptor.encrypt() for
        consistent downstream processing.
        """
        if self.output_dir is None:
            out_dir = os.path.dirname(os.path.abspath(input_wav_path))
        else:
            out_dir = self.output_dir
            os.makedirs(out_dir, exist_ok=True)

        if output_prefix is None:
            base = os.path.splitext(os.path.basename(input_wav_path))[0]
            output_prefix = f"rossler_{base}"

        print("\n" + "="*60)
        print("  RÖSSLER ENCRYPTOR — ENCRYPTION PIPELINE")
        print("="*60)

        # ── Step 1: Load audio ────────────────────────────────────────────
        sample_rate, plaintext = self._load_audio(input_wav_path)
        n_samples = len(plaintext)

        # ── Step 2: Generate chaotic trajectory ───────────────────────────
        print("\n[Step 2/5] Generating Rössler chaotic trajectory...")
        x_arr, y_arr, z_arr = self.generator.generate(n_samples)

        # ── Step 3: Extract keystream ─────────────────────────────────────
        print("\n[Step 3/5] Extracting keystream (phase-space projection)...")
        keystream = self.extractor.extract(x_arr, y_arr, z_arr)

        # ── Step 4: XOR encryption ────────────────────────────────────────
        print("\n[Step 4/5] Encrypting: C[n] = P[n] XOR K[n]...")
        p_uint    = plaintext.view(np.uint16)
        k_uint    = keystream.view(np.uint16)
        c_uint    = np.bitwise_xor(p_uint, k_uint)
        ciphertext = c_uint.view(np.int16)

        # ── Step 5: Save outputs ──────────────────────────────────────────
        print("\n[Step 5/5] Saving outputs...")

        enc_path   = os.path.join(out_dir, f"{output_prefix}_encrypted.wav")
        key_path   = os.path.join(out_dir, f"{output_prefix}_secret_key.npy")
        drive_path = os.path.join(out_dir, f"{output_prefix}_drive_signal.npy")
        plot_path  = os.path.join(out_dir, f"{output_prefix}_encrypt_plot.png")

        wavfile.write(enc_path, sample_rate, ciphertext)
        np.save(key_path,   self.generator.get_initial_conditions())
        np.save(drive_path, x_arr)

        print(f"  Encrypted audio  → {enc_path}")
        print(f"  Secret key       → {key_path}")
        print(f"  Drive signal     → {drive_path}")

        self._plot_comparison(plaintext, ciphertext, sample_rate, plot_path)
        print(f"  Comparison plot  → {plot_path}")

        print("\n[RosslerEncryptor] Encryption complete ✓")

        return {
            'plaintext'   : plaintext,
            'ciphertext'  : ciphertext,
            'keystream'   : keystream,
            'drive_signal': x_arr,
            'sample_rate' : sample_rate,
            'enc_path'    : enc_path,
            'key_path'    : key_path,
            'drive_path'  : drive_path,
        }

    # ─────────────────────────────────────────────────────────────────────
    # VISUALIZATION
    # ─────────────────────────────────────────────────────────────────────

    def _plot_comparison(self, plaintext, ciphertext, sample_rate, save_path):
        """
        Four-panel waveform + spectrogram comparison plot.
        Uses Rössler color scheme (orchid/purple) to distinguish
        from Chua plots in thesis documentation.
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 8))
        t        = np.arange(len(plaintext)) / sample_rate
        plot_len = min(len(plaintext), sample_rate * 2)

        # ── Waveforms ─────────────────────────────────────────────────────
        axes[0, 0].plot(t[:plot_len],
                        plaintext[:plot_len].astype(np.float32) / 32768,
                        lw=0.4, color='steelblue')
        axes[0, 0].set_title("Original Audio — Waveform", fontweight='bold')
        axes[0, 0].set_xlabel("Time (s)"); axes[0, 0].set_ylabel("Amplitude")
        axes[0, 0].grid(True, alpha=0.3); axes[0, 0].set_ylim(-1.1, 1.1)

        axes[0, 1].plot(t[:plot_len],
                        ciphertext[:plot_len].astype(np.float32) / 32768,
                        lw=0.4, color='darkorchid')
        axes[0, 1].set_title("Rössler Encrypted — Waveform", fontweight='bold')
        axes[0, 1].set_xlabel("Time (s)"); axes[0, 1].set_ylabel("Amplitude")
        axes[0, 1].grid(True, alpha=0.3); axes[0, 1].set_ylim(-1.1, 1.1)

        # ── Spectrograms ──────────────────────────────────────────────────
        axes[1, 0].specgram(plaintext.astype(np.float32),
                            Fs=sample_rate, cmap='viridis',
                            NFFT=512, noverlap=256)
        axes[1, 0].set_title("Original — Spectrogram", fontweight='bold')
        axes[1, 0].set_xlabel("Time (s)"); axes[1, 0].set_ylabel("Freq (Hz)")

        axes[1, 1].specgram(ciphertext.astype(np.float32),
                            Fs=sample_rate, cmap='magma',
                            NFFT=512, noverlap=256)
        axes[1, 1].set_title("Rössler Encrypted — Spectrogram\n"
                              "(should be flat/broadband)", fontweight='bold')
        axes[1, 1].set_xlabel("Time (s)"); axes[1, 1].set_ylabel("Freq (Hz)")

        plt.suptitle("Rössler System Encryption — Transmitter Output",
                     fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND-LINE INTERFACE
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Rössler System Audio Encryptor — TRANSMITTER SIDE")
    parser.add_argument("--input",  required=True,
                        help="Path to input .wav file")
    parser.add_argument("--x0",    type=float, default=1.0)
    parser.add_argument("--y0",    type=float, default=1.0)
    parser.add_argument("--z0",    type=float, default=1.0)
    parser.add_argument("--outdir", default=None)
    args = parser.parse_args()

    enc = RosslerEncryptor(x0=args.x0, y0=args.y0, z0=args.z0,
                            output_dir=args.outdir)
    enc.encrypt(args.input)
