"""
Diagnostic Script to Find the Problem
This will help identify why BER is high
"""

import numpy as np
from scipy.io import wavfile
import os
import sys

print("="*80)
print("DIAGNOSTIC SCRIPT - Finding the Problem")
print("="*80)

# Change to chua_system directory
os.chdir('chua_system')

# Check if files exist
print("\n1. Checking if required files exist...")
files_to_check = [
    'encrypted_audio.wav',
    'encrypted_audio_secret_key.txt',
    'encrypted_audio_drive_signal.npy',
    '../test_audio/test_tone.wav'
]

for f in files_to_check:
    exists = "✓" if os.path.exists(f) else "✗"
    print(f"  {exists} {f}")

# Load and compare file sizes
print("\n2. Checking file sizes...")
try:
    sr1, enc = wavfile.read('encrypted_audio.wav')
    sr2, orig = wavfile.read('../test_audio/test_tone.wav')
    drive = np.load('encrypted_audio_drive_signal.npy')
    
    print(f"  Original audio: {len(orig)} samples at {sr2} Hz")
    print(f"  Encrypted audio: {len(enc)} samples at {sr1} Hz")
    print(f"  Drive signal: {len(drive)} samples")
    
    if len(orig) != len(enc):
        print("  ✗ WARNING: Original and encrypted have different lengths!")
    if len(enc) != len(drive):
        print("  ✗ WARNING: Encrypted and drive signal have different lengths!")
    
except Exception as e:
    print(f"  ✗ Error loading files: {e}")
    sys.exit(1)

# Test encryption/decryption with simple data
print("\n3. Testing with simple known data...")
sys.path.insert(0, '.')
from chua_chaotic_generator import ChuaGenerator
from chua_keystream_extractor import ChuaKeystreamExtractor

# Generate a small keystream
gen = ChuaGenerator(x0=0.1, y0=0.0, z0=0.0)
states = gen.generate(100)
extractor = ChuaKeystreamExtractor()
keystream = extractor.extract(states, enhance=True)

print(f"  Generated {len(keystream)} keystream samples")
print(f"  Keystream range: {np.min(keystream)} to {np.max(keystream)}")
print(f"  Keystream mean: {np.mean(keystream.astype(np.float64)):.2f}")

# Test XOR operation
test_data = np.array([1000, 2000, 3000, 4000, 5000], dtype=np.int16)
test_key = keystream[:5]
encrypted = np.bitwise_xor(test_data, test_key)
decrypted = np.bitwise_xor(encrypted, test_key)

if np.array_equal(test_data, decrypted):
    print("  ✓ XOR encryption/decryption works correctly")
else:
    print("  ✗ XOR encryption/decryption FAILED!")
    print(f"    Original: {test_data}")
    print(f"    Decrypted: {decrypted}")

# Check if keystreams match
print("\n4. Comparing transmitter and receiver keystreams...")
from chua_decryptor import ChuaDecryptor

# Load drive signal
drive_signal = np.load('encrypted_audio_drive_signal.npy')

# Generate transmitter keystream
gen_tx = ChuaGenerator(x0=0.1, y0=0.0, z0=0.0)
states_tx = gen_tx.generate(min(1000, len(drive_signal)))
keystream_tx = extractor.extract(states_tx, enhance=True)

# Generate receiver keystream using Pecora-Carroll
decryptor = ChuaDecryptor(x0=0.1, y0=0.0, z0=0.0)
keystream_rx, states_rx = decryptor.synchronize_and_generate_keystream(drive_signal[:min(1000, len(drive_signal))])

# Compare first 100 samples
comparison_len = min(100, len(keystream_tx), len(keystream_rx))
matches = np.sum(keystream_tx[:comparison_len] == keystream_rx[:comparison_len])
match_percent = (matches / comparison_len) * 100

print(f"  Comparing first {comparison_len} samples:")
print(f"  Matches: {matches}/{comparison_len} ({match_percent:.1f}%)")

if match_percent < 90:
    print("  ✗ PROBLEM FOUND: Keystreams don't match!")
    print("  This means synchronization is not working.")
    print("\n  Transmitter keystream (first 10):", keystream_tx[:10])
    print("  Receiver keystream (first 10):", keystream_rx[:10])
else:
    print("  ✓ Keystreams match well")

# Check state synchronization
print("\n5. Checking state synchronization...")
state_diff_y = np.abs(states_tx[:comparison_len, 1] - states_rx[:comparison_len, 1])
state_diff_z = np.abs(states_tx[:comparison_len, 2] - states_rx[:comparison_len, 2])

print(f"  Y state difference: mean={np.mean(state_diff_y):.6f}, max={np.max(state_diff_y):.6f}")
print(f"  Z state difference: mean={np.mean(state_diff_z):.6f}, max={np.max(state_diff_z):.6f}")

if np.mean(state_diff_y) > 0.1 or np.mean(state_diff_z) > 0.1:
    print("  ✗ PROBLEM: States are not synchronizing!")
else:
    print("  ✓ States are synchronizing well")

print("\n" + "="*80)
print("DIAGNOSIS COMPLETE")
print("="*80)
print("\nIf keystreams don't match, the problem is in the synchronization.")
print("If keystreams match but BER is high, the problem is in file handling.")

# Made with Bob
