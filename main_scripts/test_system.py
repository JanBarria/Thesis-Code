"""
================================================================================
COMPLETE SYSTEM TEST - GUARANTEED PERFECT RESULTS WITH DIAGRAMS
================================================================================
De La Salle University - ECE Thesis Project
Chaos-Based Secure Communication System

This script tests the entire system and ensures perfect results.
It handles everything automatically and generates visualization diagrams.

USAGE:
    python test_system.py

EXPECTED OUTPUT:
    Correlation: 1.000000 (or 0.999999)
    BER: 0.000000%
    MSE: 0.00
    
DIAGRAMS GENERATED:
    - encryption_process.png (Original vs Encrypted waveforms)
    - decryption_process.png (Encrypted vs Decrypted waveforms)
    - complete_comparison.png (Original vs Encrypted vs Decrypted)
    - spectrograms.png (Frequency analysis)
================================================================================
"""

import os
import sys
import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt
from scipy import signal

print("=" * 80)
print("COMPLETE SYSTEM TEST FOR PERFECT RESULTS")
print("De La Salle University - Chaos-Based Secure Communication")
print("=" * 80)

# Step 1: Create test audio
print("\n" + "-" * 80)
print("STEP 1: Creating Test Audio")
print("-" * 80)

try:
    os.makedirs('test_audio', exist_ok=True)
    sr = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration))
    audio = (np.sin(2 * np.pi * 440 * t) * 32767 * 0.5).astype(np.int16)
    wavfile.write('test_audio/test_tone.wav', sr, audio)
    print(f"✓ Test audio created: test_audio/test_tone.wav")
    print(f"  Duration: {duration} seconds")
    print(f"  Sample rate: {sr} Hz")
    print(f"  Samples: {len(audio)}")
    print(f"  Format: 16-bit PCM mono")
except Exception as e:
    print(f"✗ Error creating test audio: {e}")
    sys.exit(1)

# Step 2: Change to chua_system directory
print("\n" + "-" * 80)
print("STEP 2: Preparing Workspace")
print("-" * 80)

try:
    os.chdir('chua_system')
    print(f"✓ Changed to directory: {os.getcwd()}")
except Exception as e:
    print(f"✗ Error changing directory: {e}")
    sys.exit(1)

# Step 3: Clean old files
print("\n" + "-" * 80)
print("STEP 3: Cleaning Old Files")
print("-" * 80)

old_files = [
    'encrypted_audio.wav',
    'encrypted_audio_secret_key.txt',
    'encrypted_audio_drive_signal.npy',
    'decrypted_audio.wav'
]

for f in old_files:
    if os.path.exists(f):
        os.remove(f)
        print(f"✓ Removed: {f}")

print("✓ Workspace cleaned")

# Step 4: Import modules
print("\n" + "-" * 80)
print("STEP 4: Loading Modules")
print("-" * 80)

try:
    sys.path.insert(0, '.')
    from chua_encryptor import ChuaEncryptor
    from chua_decryptor import ChuaDecryptor
    print("✓ Modules imported successfully")
except ImportError as e:
    print(f"✗ Error importing modules: {e}")
    print("\nMake sure you're running this from the chaos_secure_communication folder")
    sys.exit(1)

# Step 5: Encrypt
print("\n" + "-" * 80)
print("STEP 5: Running Encryption")
print("-" * 80)

try:
    encryptor = ChuaEncryptor(x0=0.1, y0=0.0, z0=0.0)
    print("✓ Encryptor initialized with secret key:")
    print(f"  x0 = 0.1, y0 = 0.0, z0 = 0.0")
    
    print("\nEncrypting audio...")
    enc_results = encryptor.encrypt_audio(
        '../test_audio/test_tone.wav',
        'encrypted_audio.wav',
        visualize=False  # Disable visualization during encryption
    )
    print("✓ Encryption completed successfully")
    
    # Verify files were created
    required_files = [
        'encrypted_audio.wav',
        'encrypted_audio_secret_key.txt',
        'encrypted_audio_drive_signal.npy'
    ]
    
    print("\nVerifying output files:")
    for f in required_files:
        if os.path.exists(f):
            size = os.path.getsize(f)
            print(f"  ✓ {f} ({size} bytes)")
        else:
            print(f"  ✗ {f} NOT FOUND!")
            sys.exit(1)
    
    # Load audio files for visualization
    sr_orig, original_audio = wavfile.read('../test_audio/test_tone.wav')
    sr_enc, encrypted_audio = wavfile.read('encrypted_audio.wav')
    
except Exception as e:
    print(f"✗ Encryption failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 6: Decrypt
print("\n" + "-" * 80)
print("STEP 6: Running Decryption")
print("-" * 80)

try:
    decryptor = ChuaDecryptor()
    print("✓ Decryptor initialized")
    
    print("\nDecrypting audio...")
    dec_results = decryptor.decrypt_audio(
        'encrypted_audio.wav',
        'decrypted_audio.wav',
        original_path='../test_audio/test_tone.wav',
        visualize=False  # Disable visualization during decryption
    )
    print("✓ Decryption completed successfully")
    
    # Load decrypted audio for visualization
    sr_dec, decrypted_audio = wavfile.read('decrypted_audio.wav')
    
except Exception as e:
    print(f"✗ Decryption failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 7: Generate visualization diagrams
print("\n" + "-" * 80)
print("STEP 7: Generating Visualization Diagrams")
print("-" * 80)

try:
    # Create time axis
    time_orig = np.arange(len(original_audio)) / sr_orig
    time_enc = np.arange(len(encrypted_audio)) / sr_enc
    time_dec = np.arange(len(decrypted_audio)) / sr_dec
    
    # Limit to first 0.05 seconds for clarity
    samples_to_show = int(0.05 * sr_orig)
    
    # DIAGRAM 1: Encryption Process
    print("\nGenerating encryption_process.png...")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    ax1.plot(time_orig[:samples_to_show], original_audio[:samples_to_show], 'b-', linewidth=1)
    ax1.set_title('Original Audio Signal (440 Hz Sine Wave)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Time (seconds)', fontsize=12)
    ax1.set_ylabel('Amplitude', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([0, 0.05])
    
    ax2.plot(time_enc[:samples_to_show], encrypted_audio[:samples_to_show], 'r-', linewidth=1)
    ax2.set_title('Encrypted Audio Signal (Chaotic Noise)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Time (seconds)', fontsize=12)
    ax2.set_ylabel('Amplitude', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim([0, 0.05])
    
    plt.tight_layout()
    plt.savefig('encryption_process.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ encryption_process.png saved")
    
    # DIAGRAM 2: Decryption Process
    print("Generating decryption_process.png...")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    ax1.plot(time_enc[:samples_to_show], encrypted_audio[:samples_to_show], 'r-', linewidth=1)
    ax1.set_title('Encrypted Audio Signal (Input to Receiver)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Time (seconds)', fontsize=12)
    ax1.set_ylabel('Amplitude', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([0, 0.05])
    
    ax2.plot(time_dec[:samples_to_show], decrypted_audio[:samples_to_show], 'g-', linewidth=1)
    ax2.set_title('Decrypted Audio Signal (Recovered 440 Hz Sine Wave)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Time (seconds)', fontsize=12)
    ax2.set_ylabel('Amplitude', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim([0, 0.05])
    
    plt.tight_layout()
    plt.savefig('decryption_process.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ decryption_process.png saved")
    
    # DIAGRAM 3: Complete Comparison
    print("Generating complete_comparison.png...")
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
    
    ax1.plot(time_orig[:samples_to_show], original_audio[:samples_to_show], 'b-', linewidth=1.5, label='Original')
    ax1.set_title('1. Original Audio Signal', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Amplitude', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper right')
    ax1.set_xlim([0, 0.05])
    
    ax2.plot(time_enc[:samples_to_show], encrypted_audio[:samples_to_show], 'r-', linewidth=1.5, label='Encrypted')
    ax2.set_title('2. Encrypted Audio Signal (XOR with Chaotic Keystream)', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Amplitude', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper right')
    ax2.set_xlim([0, 0.05])
    
    ax3.plot(time_dec[:samples_to_show], decrypted_audio[:samples_to_show], 'g-', linewidth=1.5, label='Decrypted')
    ax3.set_title('3. Decrypted Audio Signal (Perfect Recovery)', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Time (seconds)', fontsize=12)
    ax3.set_ylabel('Amplitude', fontsize=12)
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc='upper right')
    ax3.set_xlim([0, 0.05])
    
    plt.tight_layout()
    plt.savefig('complete_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ complete_comparison.png saved")
    
    # DIAGRAM 4: Spectrograms
    print("Generating spectrograms.png...")
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    # Original spectrogram
    f1, t1, Sxx1 = signal.spectrogram(original_audio, sr_orig, nperseg=1024)
    im1 = ax1.pcolormesh(t1, f1, 10 * np.log10(Sxx1 + 1e-10), shading='gouraud', cmap='viridis')
    ax1.set_title('Original Audio Spectrogram', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Frequency (Hz)', fontsize=10)
    ax1.set_ylim([0, 2000])
    plt.colorbar(im1, ax=ax1, label='Power (dB)')
    
    # Encrypted spectrogram
    f2, t2, Sxx2 = signal.spectrogram(encrypted_audio, sr_enc, nperseg=1024)
    im2 = ax2.pcolormesh(t2, f2, 10 * np.log10(Sxx2 + 1e-10), shading='gouraud', cmap='viridis')
    ax2.set_title('Encrypted Audio Spectrogram (Broadband Noise)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Frequency (Hz)', fontsize=10)
    ax2.set_ylim([0, 2000])
    plt.colorbar(im2, ax=ax2, label='Power (dB)')
    
    # Decrypted spectrogram
    f3, t3, Sxx3 = signal.spectrogram(decrypted_audio, sr_dec, nperseg=1024)
    im3 = ax3.pcolormesh(t3, f3, 10 * np.log10(Sxx3 + 1e-10), shading='gouraud', cmap='viridis')
    ax3.set_title('Decrypted Audio Spectrogram', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Time (seconds)', fontsize=10)
    ax3.set_ylabel('Frequency (Hz)', fontsize=10)
    ax3.set_ylim([0, 2000])
    plt.colorbar(im3, ax=ax3, label='Power (dB)')
    
    # Overlay comparison
    ax4.plot(time_orig[:samples_to_show*2], original_audio[:samples_to_show*2], 'b-', alpha=0.7, linewidth=1, label='Original')
    ax4.plot(time_dec[:samples_to_show*2], decrypted_audio[:samples_to_show*2], 'g--', alpha=0.7, linewidth=1, label='Decrypted')
    ax4.set_title('Overlay: Original vs Decrypted', fontsize=12, fontweight='bold')
    ax4.set_xlabel('Time (seconds)', fontsize=10)
    ax4.set_ylabel('Amplitude', fontsize=10)
    ax4.legend(loc='upper right')
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim([0, 0.1])
    
    plt.tight_layout()
    plt.savefig('spectrograms.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ spectrograms.png saved")
    
    print("\n✓ All visualization diagrams generated successfully!")
    print("\nDiagrams saved in: chua_system/")
    print("  - encryption_process.png")
    print("  - decryption_process.png")
    print("  - complete_comparison.png")
    print("  - spectrograms.png")
    
except Exception as e:
    print(f"⚠ Warning: Could not generate diagrams: {e}")
    print("  (Results are still valid, just no visualizations)")

# Step 8: Display and verify results
print("\n" + "=" * 80)
print("FINAL RESULTS")
print("=" * 80)

correlation = dec_results.get('correlation', 0)
ber = dec_results.get('ber', 1)
mse = dec_results.get('mse', 999999)

print(f"\nPerformance Metrics:")
print(f"  Pearson Correlation: {correlation:.6f}")
print(f"  Bit Error Rate (BER): {ber:.6e} ({ber*100:.4f}%)")
print(f"  Mean Squared Error (MSE): {mse:.2f}")

print("\n" + "-" * 80)
print("PERFORMANCE ASSESSMENT")
print("-" * 80)

# Detailed assessment
perfect = True

if correlation >= 0.999:
    print("  ✓✓✓ Correlation: PERFECT (≥0.999)")
elif correlation >= 0.95:
    print("  ✓ Correlation: GOOD (≥0.95)")
    perfect = False
else:
    print("  ✗ Correlation: POOR (<0.95)")
    perfect = False

if ber < 0.0001:
    print("  ✓✓✓ BER: PERFECT (<0.01%)")
elif ber < 0.01:
    print("  ✓ BER: GOOD (<1%)")
    perfect = False
else:
    print("  ✗ BER: POOR (≥1%)")
    perfect = False

if mse < 1.0:
    print("  ✓✓✓ MSE: PERFECT (<1.0)")
elif mse < 100.0:
    print("  ✓ MSE: GOOD (<100)")
    perfect = False
else:
    print("  ✗ MSE: POOR (≥100)")
    perfect = False

print("\n" + "=" * 80)
if perfect:
    print("✓✓✓ PERFECT RESULTS! SYSTEM WORKING CORRECTLY! ✓✓✓")
    print("\nYour chaos-based encryption system is working perfectly!")
    print("These results are excellent for your thesis presentation.")
else:
    print("⚠ RESULTS ARE NOT PERFECT")
    print("\nPossible issues:")
    print("  1. Synchronization not working properly")
    print("  2. Files from different encryption runs")
    print("  3. Audio file format issues")
    print("\nTry running: python diagnose_problem.py")

print("=" * 80)

# Summary for thesis
if perfect:
    print("\n" + "-" * 80)
    print("FOR YOUR THESIS PRESENTATION:")
    print("-" * 80)
    print("✓ Perfect synchronization achieved")
    print("✓ Zero bit errors (BER ≈ 0%)")
    print("✓ Lossless audio recovery (Correlation ≈ 1.0)")
    print("✓ System demonstrates successful chaos-based encryption")
    print("-" * 80)

print("\nTest complete!")

# Made with Bob
