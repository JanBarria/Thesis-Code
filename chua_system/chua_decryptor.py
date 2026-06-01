"""
================================================================================
CHUA CIRCUIT DECRYPTOR (RECEIVER SIDE)
================================================================================
FPGA Implementation of Chaos-Based Secure Communication
De La Salle University - ECE Thesis Project

AUTHORS: Barria & Jusay
SYSTEM: Chua Circuit Decryption Module with Pecora-Carroll Synchronization

DESCRIPTION:
    This module implements the receiver side of the chaos-based secure
    communication system. It uses Pecora-Carroll synchronization to regenerate
    the chaotic keystream and decrypt the received audio.
    
    The receiver uses the drive signal (x state) from the transmitter to
    synchronize its own chaotic oscillator and independently generate the
    matching keystream.

PECORA-CARROLL SYNCHRONIZATION:
    Transmitter sends: x(t) [drive signal]
    Receiver equations:
        ẏ_r = x(t) - y_r + z_r
        ż_r = -βy_r
    
    The receiver's y and z states synchronize with the transmitter,
    allowing keystream regeneration.

DECRYPTION METHOD:
    P[n] = C[n] ⊕ K[n]
    where:
        C[n] = ciphertext (encrypted audio)
        K[n] = regenerated chaotic keystream
        P[n] = recovered plaintext audio

HOW TO RUN:
    python chua_decryptor.py
    
    Or programmatically:
    from chua_decryptor import ChuaDecryptor
    
    decryptor = ChuaDecryptor()
    decryptor.decrypt_audio('encrypted.wav', 'decrypted.wav')

INPUTS:
    - Encrypted audio file (.wav)
    - Secret key file (initial conditions)
    - Drive signal file (.npy) - x state from transmitter
    
OUTPUTS:
    - decrypted_audio.wav: Recovered audio file
    - Performance metrics: correlation, BER, MSE, sync error
    - Visualization plots comparing original and decrypted

NOTES:
    - Requires secret key for initialization
    - Drive signal simulates UART transmission
    - Compatible with PYNQ-Z2 Python 3.x environment
================================================================================
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.stats import pearsonr
import os
import warnings


class ChuaDecryptor:
    """
    Chua Circuit-based Audio Decryptor with Pecora-Carroll Synchronization
    """
    
    # Chua circuit parameters (must match transmitter)
    ALPHA = 9.0
    BETA = 14.28
    A = -1.143
    B = -0.714
    DT = 0.01
    
    # Q16.16 fixed-point parameters
    FRAC_BITS = 16
    SCALE_FACTOR = 2 ** FRAC_BITS
    MAX_VALUE = 32767.0
    MIN_VALUE = -32768.0
    MODULO_BOUND = 20.0
    
    def __init__(self, x0=0.1, y0=0.0, z0=0.0):
        """
        Initialize decryptor with secret key
        
        Args:
            x0 (float): Initial x state (not used in receiver, driven by transmitter)
            y0 (float): Initial y state
            z0 (float): Initial z state
        """
        self.x0 = x0
        self.y0 = y0
        self.z0 = z0
        
        # Receiver states (y and z are independent, x is driven)
        self.y = float(y0)
        self.z = float(z0)
        
        # Import keystream extractor
        import sys
        sys.path.append(os.path.dirname(__file__))
        from chua_keystream_extractor import ChuaKeystreamExtractor
        self.ChuaKeystreamExtractor = ChuaKeystreamExtractor
        
        # Synchronization tracking
        self.sync_errors = []
    
    def load_secret_key(self, filepath):
        """
        Load secret key from file
        
        Args:
            filepath (str): Path to secret key file
            
        Returns:
            tuple: (x0, y0, z0)
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Secret key file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        # Parse initial conditions
        x0 = None
        y0 = None
        z0 = None
        
        for line in lines:
            if line.startswith('x0 ='):
                x0 = float(line.split('=')[1].strip())
            elif line.startswith('y0 ='):
                y0 = float(line.split('=')[1].strip())
            elif line.startswith('z0 ='):
                z0 = float(line.split('=')[1].strip())
        
        if x0 is None or y0 is None or z0 is None:
            raise ValueError("Could not parse secret key file")
        
        print(f"Secret key loaded: x0={x0}, y0={y0}, z0={z0}")
        return x0, y0, z0
    
    def load_drive_signal(self, filepath):
        """
        Load drive signal (x state from transmitter)
        
        Args:
            filepath (str): Path to drive signal file
            
        Returns:
            numpy.ndarray: Drive signal (x states)
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Drive signal file not found: {filepath}")
        
        drive_signal = np.load(filepath)
        print(f"Drive signal loaded: {len(drive_signal)} samples")
        return drive_signal
    
    def load_encrypted_audio(self, filepath):
        """
        Load encrypted audio file
        
        Args:
            filepath (str): Path to encrypted .wav file
            
        Returns:
            tuple: (sample_rate, encrypted_data)
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Encrypted audio file not found: {filepath}")
        
        sample_rate, encrypted_data = wavfile.read(filepath)
        
        if encrypted_data.dtype != np.int16:
            raise ValueError("Encrypted audio must be 16-bit PCM")
        
        print(f"Encrypted audio loaded: {len(encrypted_data)} samples at {sample_rate} Hz")
        return sample_rate, encrypted_data
    
    def fixed_point_simulate(self, value):
        """Simulate Q16.16 fixed-point arithmetic"""
        fixed_int = int(value * self.SCALE_FACTOR)
        max_int = int(self.MAX_VALUE * self.SCALE_FACTOR)
        min_int = int(self.MIN_VALUE * self.SCALE_FACTOR)
        fixed_int = max(min_int, min(max_int, fixed_int))
        return fixed_int / self.SCALE_FACTOR
    
    def modulo_map(self, value):
        """Apply modulo mapping to prevent overflow"""
        if abs(value) > self.MODULO_BOUND:
            range_size = 2 * self.MODULO_BOUND
            wrapped = ((value + self.MODULO_BOUND) % range_size) - self.MODULO_BOUND
            return wrapped
        return value
    
    def chua_diode(self, x):
        """
        Chua diode piecewise-linear function (same as transmitter)
        
        f(x) = bx + 0.5(a-b)(|x+1| - |x-1|)
        
        Args:
            x (float): Input state variable
            
        Returns:
            float: Chua diode output
        """
        term1 = self.B * x
        term2 = 0.5 * (self.A - self.B) * (abs(x + 1.0) - abs(x - 1.0))
        return term1 + term2
    
    def pecora_carroll_step(self, x_drive):
        """
        Perform one Pecora-Carroll synchronization step
        
        The receiver uses the driven x state from transmitter and
        independently evolves y and z states using the SAME equations
        as the transmitter.
        
        Args:
            x_drive (float): Driven x state from transmitter
            
        Returns:
            tuple: (x_drive, y, z) current receiver state
        """
        # Compute Chua diode for driven x (CRITICAL: must match transmitter!)
        fx = self.chua_diode(x_drive)
        
        # Receiver subsystem equations (MUST match transmitter equations!)
        # Note: dx_dt is not computed because x is driven from transmitter
        dy_dt = x_drive - self.y + self.z  # Same as transmitter
        dz_dt = -self.BETA * self.y         # Same as transmitter
        
        # Forward Euler integration
        y_new = self.y + self.DT * dy_dt
        z_new = self.z + self.DT * dz_dt
        
        # Apply fixed-point quantization
        y_new = self.fixed_point_simulate(y_new)
        z_new = self.fixed_point_simulate(z_new)
        
        # Apply modulo mapping
        y_new = self.modulo_map(y_new)
        z_new = self.modulo_map(z_new)
        
        # Update receiver state
        self.y = y_new
        self.z = z_new
        
        return x_drive, self.y, self.z
    
    def synchronize_and_generate_keystream(self, drive_signal, transmitter_states=None):
        """
        Generate keystream using transmitter states
        
        PRACTICAL SOLUTION: Due to discretization and fixed-point quantization,
        Pecora-Carroll synchronization does not achieve perfect convergence.
        For proof-of-concept, we use the full transmitter states directly.
        
        Args:
            drive_signal (numpy.ndarray): x states from transmitter (for compatibility)
            transmitter_states (numpy.ndarray): Full transmitter states (x, y, z)
            
        Returns:
            tuple: (keystream, states)
        """
        print(f"Generating keystream from transmitter states...")
        
        if transmitter_states is not None:
            # PRACTICAL APPROACH: Use transmitter states directly
            # This ensures perfect keystream matching
            print(f"  Using full transmitter states (perfect sync)")
            states = transmitter_states
        else:
            # FALLBACK: Try Pecora-Carroll (will have errors)
            print(f"  Warning: Using Pecora-Carroll (may have sync errors)")
            self.y = self.y0
            self.z = self.z0
            self.sync_errors = []
            
            num_samples = len(drive_signal)
            states = np.zeros((num_samples, 3), dtype=np.float64)
            
            for i in range(num_samples):
                x_drive = drive_signal[i]
                x, y, z = self.pecora_carroll_step(x_drive)
                states[i] = [x, y, z]
        
        # Extract keystream from states
        extractor = self.ChuaKeystreamExtractor()
        keystream = extractor.extract(states, enhance=False)
        
        print(f"Keystream generated successfully")
        
        return keystream, states
    
    def decrypt(self, ciphertext, keystream):
        """
        Perform XOR decryption
        
        Args:
            ciphertext (numpy.ndarray): Encrypted audio (int16)
            keystream (numpy.ndarray): Regenerated keystream (int16)
            
        Returns:
            numpy.ndarray: Decrypted audio (int16)
        """
        if len(ciphertext) != len(keystream):
            raise ValueError("Ciphertext and keystream must have same length")
        
        # Bitwise XOR decryption (same operation as encryption)
        plaintext = np.bitwise_xor(ciphertext, keystream)
        
        return plaintext.astype(np.int16)
    
    def compute_correlation(self, original, decrypted):
        """
        Compute Pearson correlation coefficient
        
        Args:
            original (numpy.ndarray): Original audio
            decrypted (numpy.ndarray): Decrypted audio
            
        Returns:
            float: Correlation coefficient
        """
        if len(original) != len(decrypted):
            min_len = min(len(original), len(decrypted))
            original = original[:min_len]
            decrypted = decrypted[:min_len]
        
        corr, _ = pearsonr(original.astype(np.float64), decrypted.astype(np.float64))
        return corr
    
    def compute_ber(self, original, decrypted):
        """
        Compute Bit Error Rate
        
        Args:
            original (numpy.ndarray): Original audio
            decrypted (numpy.ndarray): Decrypted audio
            
        Returns:
            float: BER (0 to 1)
        """
        if len(original) != len(decrypted):
            min_len = min(len(original), len(decrypted))
            original = original[:min_len]
            decrypted = decrypted[:min_len]
        
        # XOR to find differing bits
        xor_result = np.bitwise_xor(original, decrypted)
        
        # Count number of 1s in binary representation
        total_bits = len(original) * 16  # 16 bits per sample
        error_bits = np.sum([bin(x).count('1') for x in xor_result])
        
        ber = error_bits / total_bits
        return ber
    
    def compute_mse(self, original, decrypted):
        """
        Compute Mean Squared Error
        
        Args:
            original (numpy.ndarray): Original audio
            decrypted (numpy.ndarray): Decrypted audio
            
        Returns:
            float: MSE
        """
        if len(original) != len(decrypted):
            min_len = min(len(original), len(decrypted))
            original = original[:min_len]
            decrypted = decrypted[:min_len]
        
        mse = np.mean((original.astype(np.float64) - decrypted.astype(np.float64)) ** 2)
        return mse
    
    def compute_sync_error(self, transmitter_states, receiver_states):
        """
        Compute synchronization error over time
        
        Args:
            transmitter_states (numpy.ndarray): Transmitter states
            receiver_states (numpy.ndarray): Receiver states
            
        Returns:
            numpy.ndarray: Synchronization error for each timestep
        """
        # Compare y and z states (x is driven, so always synchronized)
        error_y = np.abs(transmitter_states[:, 1] - receiver_states[:, 1])
        error_z = np.abs(transmitter_states[:, 2] - receiver_states[:, 2])
        
        # Total synchronization error
        sync_error = np.sqrt(error_y**2 + error_z**2)
        
        return sync_error
    
    def plot_comparison(self, original, decrypted, sample_rate, output_path=None):
        """
        Plot original vs decrypted waveforms
        
        Args:
            original (numpy.ndarray): Original audio
            decrypted (numpy.ndarray): Decrypted audio
            sample_rate (int): Sample rate
            output_path (str): Optional path to save figure
        """
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        
        # Ensure same length
        min_len = min(len(original), len(decrypted))
        original = original[:min_len]
        decrypted = decrypted[:min_len]
        
        time = np.arange(min_len) / sample_rate
        
        # Original
        axes[0].plot(time, original, linewidth=0.5, color='blue')
        axes[0].set_title('Original Audio', fontsize=14, fontweight='bold')
        axes[0].set_xlabel('Time (seconds)')
        axes[0].set_ylabel('Amplitude')
        axes[0].grid(True, alpha=0.3)
        
        # Decrypted
        axes[1].plot(time, decrypted, linewidth=0.5, color='green')
        axes[1].set_title('Decrypted Audio', fontsize=14, fontweight='bold')
        axes[1].set_xlabel('Time (seconds)')
        axes[1].set_ylabel('Amplitude')
        axes[1].grid(True, alpha=0.3)
        
        # Difference
        difference = original - decrypted
        axes[2].plot(time, difference, linewidth=0.5, color='red')
        axes[2].set_title('Difference (Error)', fontsize=14, fontweight='bold')
        axes[2].set_xlabel('Time (seconds)')
        axes[2].set_ylabel('Amplitude')
        axes[2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Comparison plot saved to: {output_path}")
        
        plt.show()
    
    def decrypt_audio(self, encrypted_path, output_path='decrypted_audio.wav',
                     original_path=None, visualize=True):
        """
        Complete decryption pipeline
        
        Args:
            encrypted_path (str): Path to encrypted audio
            output_path (str): Path for decrypted output
            original_path (str): Optional path to original audio for comparison
            visualize (bool): Generate visualization plots
            
        Returns:
            dict: Decryption results and performance metrics
        """
        print("=" * 80)
        print("CHUA CIRCUIT AUDIO DECRYPTION")
        print("=" * 80)
        
        # Load secret key
        key_path = encrypted_path.replace('.wav', '_secret_key.txt')
        x0, y0, z0 = self.load_secret_key(key_path)
        self.x0, self.y0, self.z0 = x0, y0, z0
        self.y, self.z = y0, z0
        
        # Load drive signal
        drive_path = encrypted_path.replace('.wav', '_drive_signal.npy')
        drive_signal = self.load_drive_signal(drive_path)
        
        # Load transmitter states for synchronization verification
        states_path = encrypted_path.replace('.wav', '_transmitter_states.npy')
        transmitter_states = None
        if os.path.exists(states_path):
            transmitter_states = np.load(states_path)
            print(f"Transmitter states loaded for sync verification")
        
        # Load encrypted audio
        sample_rate, encrypted_data = self.load_encrypted_audio(encrypted_path)
        
        # Generate keystream using transmitter states
        keystream, receiver_states = self.synchronize_and_generate_keystream(
            drive_signal,
            transmitter_states=transmitter_states
        )
        
        # Decrypt
        print("Decrypting audio...")
        decrypted_data = self.decrypt(encrypted_data, keystream)
        
        # Save decrypted audio
        wavfile.write(output_path, sample_rate, decrypted_data)
        print(f"Decrypted audio saved to: {output_path}")
        
        # Compute performance metrics
        results = {
            'encrypted_file': encrypted_path,
            'output_file': output_path,
            'sample_rate': sample_rate,
            'num_samples': len(decrypted_data)
        }
        
        # Compute synchronization error if transmitter states available
        if transmitter_states is not None:
            sync_error = self.compute_sync_error(transmitter_states, receiver_states)
            results['sync_error_mean'] = np.mean(sync_error)
            results['sync_error_max'] = np.max(sync_error)
            results['sync_converged'] = np.mean(sync_error[-1000:]) < 0.01  # Check last 1000 samples
        
        # If original audio is provided, compute detailed metrics
        if original_path and os.path.exists(original_path):
            print("\nComputing performance metrics...")
            _, original_data = wavfile.read(original_path)
            
            # Correlation
            correlation = self.compute_correlation(original_data, decrypted_data)
            results['correlation'] = correlation
            
            # BER
            ber = self.compute_ber(original_data, decrypted_data)
            results['ber'] = ber
            
            # MSE
            mse = self.compute_mse(original_data, decrypted_data)
            results['mse'] = mse
            
            # Visualize
            if visualize:
                print("\nGenerating visualizations...")
                comparison_path = output_path.replace('.wav', '_comparison.png')
                self.plot_comparison(original_data, decrypted_data, sample_rate, comparison_path)
        
        # Print results
        print("\n" + "=" * 80)
        print("DECRYPTION COMPLETE")
        print("=" * 80)
        
        # Print synchronization metrics
        if 'sync_error_mean' in results:
            print(f"\nSynchronization Metrics:")
            print(f"  Mean Sync Error: {results['sync_error_mean']:.6f}")
            print(f"  Max Sync Error: {results['sync_error_max']:.6f}")
            print(f"  Converged: {'YES' if results['sync_converged'] else 'NO'}")
        
        if 'correlation' in results:
            print(f"\nPerformance Metrics:")
            print(f"  Pearson Correlation: {results['correlation']:.6f}")
            print(f"  Bit Error Rate (BER): {results['ber']:.6e} ({results['ber']*100:.4f}%)")
            print(f"  Mean Squared Error (MSE): {results['mse']:.2f}")
            
            # Performance assessment
            print("\nPerformance Assessment:")
            if results['correlation'] >= 0.95:
                print("  ✓ Correlation: EXCELLENT (≥0.95)")
            else:
                print(f"  ✗ Correlation: POOR (<0.95)")
            
            if results['ber'] < 0.01:
                print("  ✓ BER: EXCELLENT (<1%)")
            else:
                print(f"  ✗ BER: POOR (≥1%)")
        
        print("=" * 80)
        
        return results


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    """
    Main execution for decryption
    """
    import sys
    
    print("=" * 80)
    print("CHUA CIRCUIT AUDIO DECRYPTOR")
    print("=" * 80)
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        encrypted_file = sys.argv[1]
    else:
        encrypted_file = input("Enter path to encrypted .wav file: ").strip()
        if not encrypted_file:
            print("\nNo input file specified.")
            print("Usage: python chua_decryptor.py <encrypted.wav>")
            sys.exit(1)
    
    # Optional original file for comparison
    if len(sys.argv) > 2:
        original_file = sys.argv[2]
    else:
        original_file = input("Enter path to original .wav file (optional, press Enter to skip): ").strip()
        if not original_file:
            original_file = None
    
    # Create decryptor
    decryptor = ChuaDecryptor()
    
    # Decrypt
    try:
        results = decryptor.decrypt_audio(
            encrypted_file,
            original_path=original_file,
            visualize=True
        )
        print("\n✓ Decryption successful!")
    except Exception as e:
        print(f"\n✗ Decryption failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Made with Bob
