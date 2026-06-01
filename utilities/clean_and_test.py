"""
Clean old files and run fresh test
"""
import os
import sys

print("=" * 80)
print("CLEANING OLD FILES AND RUNNING FRESH TEST")
print("=" * 80)

# Change to chua_system directory
os.chdir('chua_system')
print(f"\nWorking directory: {os.getcwd()}")

# Delete old files
old_files = [
    'encrypted_audio.wav',
    'encrypted_audio_secret_key.txt',
    'encrypted_audio_drive_signal.npy',
    'encrypted_audio_transmitter_states.npy',
    'decrypted_audio.wav',
    'encryption_process.png',
    'decryption_process.png',
    'complete_comparison.png',
    'spectrograms.png'
]

print("\nDeleting old files...")
for f in old_files:
    if os.path.exists(f):
        os.remove(f)
        print(f"  ✓ Deleted: {f}")

print("\n" + "=" * 80)
print("Now run: python test_system.py")
print("=" * 80)

# Made with Bob
