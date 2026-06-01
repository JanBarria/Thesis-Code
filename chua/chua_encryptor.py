"""
================================================================================
FILE: chua_encryptor.py
SYSTEM: Chua Circuit — TRANSMITTER (Encryption Side)
================================================================================
DESCRIPTION:
    Loads a mono 16-bit PCM .wav audio file, generates a Chua chaotic
    keystream, and encrypts the audio using bitwise XOR:
        C[n] = P[n] XOR K[n]

    Saves the encrypted audio, secret key (initial conditions), and the
    drive signal (x state variable) that will be shared with the receiver
    for Pecora-Carroll synchronization.

HOW TO RUN:
    python chua_encryptor.py --input test_audio.wav

    Or import and call:
        from chua_encryptor import ChuaEncryptor
        enc = ChuaEncryptor()
        enc.encrypt("test_audio.wav")

EXPECTED INPUT:
    - Mono .wav file, 16-bit PCM (any sample rate)

EXPECTED OUTPUT:
    - encrypted_chua.wav       — encrypted audio file
    - chua_secret_key.npy      — initial conditions (secret key)
    - chua_drive_signal.npy    — x state variable for receiver sync
    - chua_encrypt_plot.png    — waveform + spectrogram comparison

PYNQ-Z2 NOTE:
    Place your .wav file on the PYNQ board via:
        scp test_audio.wav xilinx@<board_ip>:/home/xilinx/
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
from chua_chaotic_generator  import ChuaGenerator
from chua_keystream_extractor import ChuaKeystreamExtractor


class ChuaEncryptor:
    """
    Chua Circuit Transmitter — encrypts a .wav file using chaotic XOR.

    The transmitter also outputs the 'drive signal' (x state variable)
    which is shared with the receiver board to enable Pecora-Carroll
    synchronization. In a real UART deployment, this drive signal is
    sent byte-by-byte ahead of or interleaved with the ciphertext.
    """

    def __init__(self,
                 x0=0.1, y0=0.0, z0=0.0,
                 alpha=9.0, beta=14.28,
                 a=-1.143, b=-0.714,
                 dt=0.01,
                 output_dir=None):
        """
        Args:
            x0, y0, z0   : Initial conditions — this is the SECRET KEY
            alpha, beta  : System parameters
            a, b         : Chua diode slopes
            dt           : Integration time step
            output_dir   : Where to save output files (default: same as input)
        """
        self.generator  = ChuaGenerator(alpha=alpha, beta=beta,
                                         a=a, b=b, dt=dt,
                                         x0=x0, y0=y0, z0=z0)
        self.extractor  = ChuaKeystreamExtractor(use_xyz_mix=True)
        self.output_dir = output_dir

    # ─────────────────────────────────────────────────────────────────────
    # AUDIO LOADING
    # ─────────────────────────────────────────────────────────────────────

    def _load_audio(self, filepath):
        """
        Load a mono 16-bit PCM .wav file.

        Returns:
            sample_rate (int): Audio sample rate in Hz
            samples     (np.ndarray): int16 audio samples
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Audio file not found: {filepath}")

        sample_rate, samples = wavfile.read(filepath)

        # ── Handle stereo: downmix to mono ────────────────────────────────
        if samples.ndim == 2:
            print("[ChuaEncryptor] Stereo detected — downmixing to mono")
            samples = samples.mean(axis=1).astype(np.int16)

        # ── Ensure int16 ──────────────────────────────────────────────────
        if samples.dtype != np.int16:
            print(f"[ChuaEncryptor] Converting {samples.dtype} → int16")
            samples = samples.astype(np.int16)

        print(f"[ChuaEncryptor] Loaded: {filepath}")
        print(f"  Sample rate : {sample_rate} Hz")
        print(f"  Samples     : {len(samples)}")
        print(f"  Duration    : {len(samples)/sample_rate:.2f} seconds")

        return sample_rate, samples

    # ─────────────────────────────────────────────────────────────────────
    # ENCRYPTION
    # ─────────────────────────────────────────────────────────────────────

    def encrypt(self, input_wav_path, output_prefix=None):
        """
        Full encryption pipeline.

        Args:
            input_wav_path (str): Path to plaintext .wav file
            output_prefix  (str): Optional prefix for output files

        Returns:
            dict: Contains encrypted samples, keystream, drive signal,
                  file paths, and performance info
        """
        # ── Determine output directory ────────────────────────────────────
        if self.output_dir is None:
            out_dir = os.path.dirname(os.path.abspath(input_wav_path))
        else:
            out_dir = self.output_dir
            os.makedirs(out_dir, exist_ok=True)

        if output_prefix is None:
            base = os.path.splitext(os.path.basename(input_wav_path))[0]
            output_prefix = f"chua_{base}"

        # ── Step 1: Load audio ────────────────────────────────────────────
        print("\n" + "="*60)
        print("  CHUA ENCRYPTOR — ENCRYPTION PIPELINE")
        print("="*60)
        sample_rate, plaintext = self._load_audio(input_wav_path)
        n_samples = len(plaintext)

        # ── Step 2: Generate chaotic trajectory ───────────────────────────
        print("\n[Step 2/5] Generating Chua chaotic trajectory...")
        x_arr, y_arr, z_arr = self.generator.generate(n_samples)

        # ── Step 3: Extract keystream ─────────────────────────────────────
        print("\n[Step 3/5] Extracting keystream...")
        keystream = self.extractor.extract(x_arr, y_arr, z_arr)

        # ── Step 4: XOR encryption ────────────────────────────────────────
        print("\n[Step 4/5] Encrypting: C[n] = P[n] XOR K[n]...")
        # View as uint16 for XOR, then view back as int16
        p_uint = plaintext.view(np.uint16)
        k_uint = keystream.view(np.uint16)
        c_uint = np.bitwise_xor(p_uint, k_uint)
        ciphertext = c_uint.view(np.int16)

        # ── Step 5: Save outputs ──────────────────────────────────────────
        print("\n[Step 5/5] Saving outputs...")

        enc_path   = os.path.join(out_dir, f"{output_prefix}_encrypted.wav")
        key_path   = os.path.join(out_dir, f"{output_prefix}_secret_key.npy")
        drive_path = os.path.join(out_dir, f"{output_prefix}_drive_signal.npy")
        plot_path  = os.path.join(out_dir, f"{output_prefix}_encrypt_plot.png")

        wavfile.write(enc_path, sample_rate, ciphertext)
        np.save(key_path,   self.generator.get_initial_conditions())
        np.save(drive_path, x_arr)   # x is the Pecora-Carroll drive variable

        print(f"  Encrypted audio  → {enc_path}")
        print(f"  Secret key       → {key_path}")
        print(f"  Drive signal     → {drive_path}")

        # ── Plot: original vs encrypted ───────────────────────────────────
        self._plot_comparison(plaintext, ciphertext, sample_rate, plot_path)
        print(f"  Comparison plot  → {plot_path}")

        print("\n[ChuaEncryptor] Encryption complete ✓")

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
        Plot waveform and spectrogram comparison:
        original audio vs encrypted ciphertext.
        A good encryption produces a flat (broadband white noise) spectrogram.
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 8))
        t = np.arange(len(plaintext)) / sample_rate
        plot_len = min(len(plaintext), sample_rate * 2)  # show first 2 seconds

        # ── Waveforms ─────────────────────────────────────────────────────
        axes[0, 0].plot(t[:plot_len],
                        plaintext[:plot_len].astype(np.float32) / 32768,
                        lw=0.4, color='steelblue')
        axes[0, 0].set_title("Original Audio — Waveform", fontweight='bold')
        axes[0, 0].set_xlabel("Time (s)"); axes[0, 0].set_ylabel("Amplitude")
        axes[0, 0].grid(True, alpha=0.3); axes[0, 0].set_ylim(-1.1, 1.1)

        axes[0, 1].plot(t[:plot_len],
                        ciphertext[:plot_len].astype(np.float32) / 32768,
                        lw=0.4, color='crimson')
        axes[0, 1].set_title("Encrypted Audio — Waveform", fontweight='bold')
        axes[0, 1].set_xlabel("Time (s)"); axes[0, 1].set_ylabel("Amplitude")
        axes[0, 1].grid(True, alpha=0.3); axes[0, 1].set_ylim(-1.1, 1.1)

        # ── Spectrograms ──────────────────────────────────────────────────
        axes[1, 0].specgram(plaintext.astype(np.float32),
                            Fs=sample_rate, cmap='viridis',
                            NFFT=512, noverlap=256)
        axes[1, 0].set_title("Original Audio — Spectrogram", fontweight='bold')
        axes[1, 0].set_xlabel("Time (s)"); axes[1, 0].set_ylabel("Frequency (Hz)")

        axes[1, 1].specgram(ciphertext.astype(np.float32),
                            Fs=sample_rate, cmap='plasma',
                            NFFT=512, noverlap=256)
        axes[1, 1].set_title("Encrypted Audio — Spectrogram\n"
                              "(should be flat/broadband)",
                              fontweight='bold')
        axes[1, 1].set_xlabel("Time (s)"); axes[1, 1].set_ylabel("Frequency (Hz)")

        plt.suptitle("Chua Circuit Encryption — Transmitter Output",
                     fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND-LINE INTERFACE
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Chua Circuit Audio Encryptor — TRANSMITTER SIDE")
    parser.add_argument("--input",  required=True,
                        help="Path to input .wav file")
    parser.add_argument("--x0",    type=float, default=0.1,
                        help="Initial condition x0 (secret key, default 0.1)")
    parser.add_argument("--y0",    type=float, default=0.0,
                        help="Initial condition y0 (default 0.0)")
    parser.add_argument("--z0",    type=float, default=0.0,
                        help="Initial condition z0 (default 0.0)")
    parser.add_argument("--outdir", default=None,
                        help="Output directory (default: same as input)")
    args = parser.parse_args()

    encryptor = ChuaEncryptor(x0=args.x0, y0=args.y0, z0=args.z0,
                               output_dir=args.outdir)
    result = encryptor.encrypt(args.input)
