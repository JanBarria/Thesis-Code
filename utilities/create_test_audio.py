"""
Create Test Audio File
Simple script to generate a 1-second test tone for testing the encryption system.
"""

import numpy as np
from scipy.io import wavfile
import os

print("=" * 60)
print("CREATING TEST AUDIO FILE")
print("=" * 60)

# Create test_audio directory if it doesn't exist
os.makedirs('test_audio', exist_ok=True)
print("✓ test_audio directory ready")

# Generate 1-second test tone (440 Hz A4 note)
sample_rate = 44100
duration = 1.0
t = np.linspace(0, duration, int(sample_rate * duration))
audio = (np.sin(2 * np.pi * 440 * t) * 32767 * 0.5).astype(np.int16)

# Save as WAV file
output_path = 'test_audio/test_tone.wav'
wavfile.write(output_path, sample_rate, audio)

print(f"✓ Test audio created: {output_path}")
print(f"  Duration: {duration} seconds")
print(f"  Sample rate: {sample_rate} Hz")
print(f"  Frequency: 440 Hz (A4 note)")
print(f"  Samples: {len(audio)}")
print("=" * 60)
print("SUCCESS! You can now run the encryptor.")
print("=" * 60)

# Made with Bob
