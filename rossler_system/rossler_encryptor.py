"""
================================================================================
RÖSSLER SYSTEM ENCRYPTOR (TRANSMITTER SIDE)
================================================================================
FPGA Implementation of Chaos-Based Secure Communication
De La Salle University - ECE Thesis Project

AUTHORS: Cortes & Abalos
SYSTEM: Rössler System Encryption Module

DESCRIPTION:
    This module implements the transmitter side of the chaos-based secure
    communication system using the Rössler attractor. It loads a mono .wav
    audio file, generates a chaotic keystream, and performs bitwise XOR
    encryption.
    
    The encrypted audio and initial conditions (secret key) are saved for
    transmission to the receiver.

ENCRYPTION METHOD:
    C[n] = P[n] ⊕ K[n]
    where:
        P[n] = plaintext audio sample (16-bit PCM)
        K[n] = chaotic keystream (16-bit)
        C[n] = ciphertext (encrypted audio)

HOW TO RUN:
    python rossler_encryptor.py
    
    Or programmatically:
    from rossler_encryptor import RosslerEncryptor
    
    encryptor = RosslerEncryptor()
    encryptor.encrypt_audio('input.wav', 'encrypted.wav')

INPUTS:
    - Mono .wav audio file (16-bit PCM format)
    - Initial conditions (x0, y0, z0) - the secret key
    
OUTPUTS:
    - encrypted_audio.wav: Encrypted audio file
    - rossler_secret_key.txt: Initial conditions for synchronization
    - drive_signal.npy: One state variable for receiver synchronization
    - Visualization plots: waveforms and spectrograms

NOTES:
    - Audio must be mono, 16-bit PCM format
    - Sample rate is preserved in encrypted file
    - For UART transmission, use drive_signal.npy
    - Compatible with PYNQ-Z2 Python 3.x environment
================================================================================
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
import os
import warnings


class RosslerEncryptor:
    """
    Rössler System-based Audio Encryptor (Transmitter)
    """
    
    def __init__(self, x0=0.1, y0=0.0, z0=0.0):
        """
        Initialize encryptor with secret key (initial conditions)
        
        Args:
            x0 (float): Initial x state (secret key component 1)
            y0 (float): Initial y state (secret key component 2)
            z0 (float): Initial z state (secret key component 3)
        """
        self.x0 = x0
        self.y0 = y0
        self.z0 = z0
        
        # Import modules
        import sys
        sys.path.append(os.path.dirname(__file__))
        from rossler_chaotic_generator import RosslerGenerator
        from rossler_keystream_extractor import RosslerKeystreamExtractor
        
        self.RosslerGenerator = RosslerGenerator
        self.RosslerKeystreamExtractor = RosslerKeystreamExtractor
    
    def load_audio(self, filepath):
        """
        Load and validate audio file
        
        Args:
            filepath (str): Path to .wav file
            
        Returns:
            tuple: (sample_rate, audio_data)
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Audio file not found: {filepath}")
        
        # Load audio
        sample_rate, audio_data = wavfile.read(filepath)
        
        # Validate format
        if audio_data.ndim != 1:
            if audio_data.ndim == 2 and audio_data.shape[1] == 1:
                # Convert single-channel stereo to mono
                audio_data = audio_data.flatten()
            else:
                raise ValueError(
                    f"Audio must be mono. Got shape: {audio_data.shape}. "
                    "Please convert to mono first."
                )
        
        if audio_data.dtype != np.int16:
            raise ValueError(
                f"Audio must be 16-bit PCM. Got dtype: {audio_data.dtype}"
            )
        
        print(f"Loaded audio: {len(audio_data)} samples at {sample_rate} Hz")
        print(f"Duration: {len(audio_data)/sample_rate:.2f} seconds")
        
        return sample_rate, audio_data
    
    def generate_keystream(self, length):
        """
        Generate chaotic keystream
        
        Args:
            length (int): Number of keystream samples needed
            
        Returns:
            tuple: (keystream, states)
                keystream: 16-bit integer array for XOR
                states: Raw chaotic states for synchronization
        """
        print(f"Generating {length} keystream samples...")
        
        # Create generator with secret key
        generator = self.RosslerGenerator(x0=self.x0, y0=self.y0, z0=self.z0)
        
        # Generate chaotic states
        states = generator.generate(num_samples=length)
        
        # Extract keystream
        extractor = self.RosslerKeystreamExtractor()
        keystream = extractor.extract(states, enhance=True)
        
        print(f"Keystream generated successfully")
        
        return keystream, states
    
    def encrypt(self, plaintext, keystream):
        """
        Perform XOR encryption
        
        Args:
            plaintext (numpy.ndarray): Audio samples (int16)
            keystream (numpy.ndarray): Chaotic keystream (int16)
            
        Returns:
            numpy.ndarray: Encrypted audio (int16)
        """
        if len(plaintext) != len(keystream):
            raise ValueError("Plaintext and keystream must have same length")
        
        # Bitwise XOR encryption
        ciphertext = np.bitwise_xor(plaintext, keystream)
        
        return ciphertext.astype(np.int16)
    
    def save_encrypted_audio(self, filepath, sample_rate, encrypted_data):
        """
        Save encrypted audio to .wav file
        
        Args:
            filepath (str): Output file path
            sample_rate (int): Audio sample rate
            encrypted_data (numpy.ndarray): Encrypted audio samples
        """
        wavfile.write(filepath, sample_rate, encrypted_data)
        print(f"Encrypted audio saved to: {filepath}")
    
    def save_secret_key(self, filepath):
        """
        Save initial conditions (secret key) to file
        
        Args:
            filepath (str): Output file path
        """
        with open(filepath, 'w') as f:
            f.write("RÖSSLER SYSTEM SECRET KEY (Initial Conditions)\n")
            f.write("=" * 60 + "\n")
            f.write(f"x0 = {self.x0}\n")
            f.write(f"y0 = {self.y0}\n")
            f.write(f"z0 = {self.z0}\n")
            f.write("=" * 60 + "\n")
            f.write("IMPORTANT: Keep this file secure!\n")
            f.write("The receiver needs these values for decryption.\n")
        
        print(f"Secret key saved to: {filepath}")
    
    def save_drive_signal(self, filepath, states):
        """
        Save drive signal for Pecora-Carroll synchronization
        
        For Rössler system, we transmit the x state variable
        
        Args:
            filepath (str): Output file path
            states (numpy.ndarray): Chaotic states array
        """
        # Extract x state (first column)
        drive_signal = states[:, 0]
        
        # Save as numpy array
        np.save(filepath, drive_signal)
        print(f"Drive signal (x state) saved to: {filepath}")
        print(f"  Shape: {drive_signal.shape}")
        print(f"  This will be transmitted via UART to receiver")
    
    def plot_waveforms(self, original, encrypted, sample_rate, output_path=None):
        """
        Plot original vs encrypted waveforms
        
        Args:
            original (numpy.ndarray): Original audio
            encrypted (numpy.ndarray): Encrypted audio
            sample_rate (int): Sample rate
            output_path (str): Optional path to save figure
        """
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        
        # Time axis
        time = np.arange(len(original)) / sample_rate
        
        # Plot original
        axes[0].plot(time, original, linewidth=0.5)
        axes[0].set_title('Original Audio Waveform', fontsize=14, fontweight='bold')
        axes[0].set_xlabel('Time (seconds)')
        axes[0].set_ylabel('Amplitude')
        axes[0].grid(True, alpha=0.3)
        axes[0].set_xlim([0, time[-1]])
        
        # Plot encrypted
        axes[1].plot(time, encrypted, linewidth=0.5, color='red')
        axes[1].set_title('Encrypted Audio Waveform', fontsize=14, fontweight='bold')
        axes[1].set_xlabel('Time (seconds)')
        axes[1].set_ylabel('Amplitude')
        axes[1].grid(True, alpha=0.3)
        axes[1].set_xlim([0, time[-1]])
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Waveform plot saved to: {output_path}")
        
        plt.show()
    
    def plot_spectrograms(self, original, encrypted, sample_rate, output_path=None):
        """
        Plot spectrograms to verify encryption (should show broadband noise)
        
        Args:
            original (numpy.ndarray): Original audio
            encrypted (numpy.ndarray): Encrypted audio
            sample_rate (int): Sample rate
            output_path (str): Optional path to save figure
        """
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        
        # Original spectrogram
        axes[0].specgram(original, Fs=sample_rate, NFFT=1024, noverlap=512, cmap='viridis')
        axes[0].set_title('Original Audio Spectrogram', fontsize=14, fontweight='bold')
        axes[0].set_xlabel('Time (seconds)')
        axes[0].set_ylabel('Frequency (Hz)')
        
        # Encrypted spectrogram (should be noise-like)
        axes[1].specgram(encrypted, Fs=sample_rate, NFFT=1024, noverlap=512, cmap='viridis')
        axes[1].set_title('Encrypted Audio Spectrogram (Broadband Noise)', 
                         fontsize=14, fontweight='bold')
        axes[1].set_xlabel('Time (seconds)')
        axes[1].set_ylabel('Frequency (Hz)')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Spectrogram plot saved to: {output_path}")
        
        plt.show()
    
    def encrypt_audio(self, input_path, output_path='encrypted_audio.wav', 
                     visualize=True):
        """
        Complete encryption pipeline
        
        Args:
            input_path (str): Path to input .wav file
            output_path (str): Path for encrypted output
            visualize (bool): Generate visualization plots
            
        Returns:
            dict: Encryption results and metadata
        """
        print("=" * 80)
        print("RÖSSLER SYSTEM AUDIO ENCRYPTION")
        print("=" * 80)
        
        # Load audio
        sample_rate, audio_data = self.load_audio(input_path)
        
        # Generate keystream
        keystream, states = self.generate_keystream(len(audio_data))
        
        # Encrypt
        print("Encrypting audio...")
        encrypted_data = self.encrypt(audio_data, keystream)
        
        # Save outputs
        self.save_encrypted_audio(output_path, sample_rate, encrypted_data)
        
        # Save secret key
        key_path = output_path.replace('.wav', '_secret_key.txt')
        self.save_secret_key(key_path)
        
        # Save drive signal for synchronization
        drive_path = output_path.replace('.wav', '_drive_signal.npy')
        self.save_drive_signal(drive_path, states)
        
        # Visualize
        if visualize:
            print("\nGenerating visualizations...")
            
            # Waveforms
            waveform_path = output_path.replace('.wav', '_waveforms.png')
            self.plot_waveforms(audio_data, encrypted_data, sample_rate, waveform_path)
            
            # Spectrograms
            spectrogram_path = output_path.replace('.wav', '_spectrograms.png')
            self.plot_spectrograms(audio_data, encrypted_data, sample_rate, spectrogram_path)
        
        # Compute statistics
        results = {
            'input_file': input_path,
            'output_file': output_path,
            'sample_rate': sample_rate,
            'num_samples': len(audio_data),
            'duration_seconds': len(audio_data) / sample_rate,
            'secret_key': (self.x0, self.y0, self.z0),
            'original_mean': np.mean(audio_data.astype(np.float64)),
            'original_std': np.std(audio_data.astype(np.float64)),
            'encrypted_mean': np.mean(encrypted_data.astype(np.float64)),
            'encrypted_std': np.std(encrypted_data.astype(np.float64))
        }
        
        print("\n" + "=" * 80)
        print("ENCRYPTION COMPLETE")
        print("=" * 80)
        print(f"Original audio mean: {results['original_mean']:.2f}")
        print(f"Encrypted audio mean: {results['encrypted_mean']:.2f}")
        print(f"Original audio std: {results['original_std']:.2f}")
        print(f"Encrypted audio std: {results['encrypted_std']:.2f}")
        print("\nFiles generated:")
        print(f"  1. {output_path}")
        print(f"  2. {key_path}")
        print(f"  3. {drive_path}")
        if visualize:
            print(f"  4. {waveform_path}")
            print(f"  5. {spectrogram_path}")
        print("=" * 80)
        
        return results


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    """
    Main execution for encryption
    """
    import sys
    
    print("=" * 80)
    print("RÖSSLER SYSTEM AUDIO ENCRYPTOR")
    print("=" * 80)
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        # Default test file
        input_file = input("Enter path to input .wav file: ").strip()
        if not input_file:
            print("\nNo input file specified.")
            print("Usage: python rossler_encryptor.py <input.wav>")
            print("\nFor testing, you can create a test audio file first.")
            sys.exit(1)
    
    # Secret key (initial conditions)
    print("\nUsing default secret key:")
    print("  x0 = 0.1")
    print("  y0 = 0.0")
    print("  z0 = 0.0")
    print("(You can modify these in the code for different keys)")
    
    # Create encryptor
    encryptor = RosslerEncryptor(x0=0.1, y0=0.0, z0=0.0)
    
    # Encrypt
    try:
        results = encryptor.encrypt_audio(input_file, visualize=True)
        print("\n✓ Encryption successful!")
    except Exception as e:
        print(f"\n✗ Encryption failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Made with Bob
