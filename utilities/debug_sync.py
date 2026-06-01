"""
Debug synchronization by comparing transmitter and receiver states
"""
import numpy as np
import sys
import os

os.chdir('chua_system')
sys.path.append('.')

from chua_chaotic_generator import ChuaGenerator
from chua_keystream_extractor import ChuaKeystreamExtractor

print("=" * 80)
print("DEBUGGING SYNCHRONIZATION")
print("=" * 80)

# Generate transmitter states
print("\n1. Generating transmitter states...")
tx_gen = ChuaGenerator(x0=0.1, y0=0.0, z0=0.0)
tx_states = tx_gen.generate(num_samples=1000)
print(f"   Transmitter states shape: {tx_states.shape}")
print(f"   TX state[0]: x={tx_states[0,0]:.6f}, y={tx_states[0,1]:.6f}, z={tx_states[0,2]:.6f}")
print(f"   TX state[999]: x={tx_states[999,0]:.6f}, y={tx_states[999,1]:.6f}, z={tx_states[999,2]:.6f}")

# Simulate receiver with Pecora-Carroll
print("\n2. Simulating receiver with Pecora-Carroll...")
from chua_decryptor import ChuaDecryptor
rx = ChuaDecryptor(x0=0.1, y0=0.0, z0=0.0)

# Extract drive signal (x states)
drive_signal = tx_states[:, 0]

# Synchronize
rx_keystream, rx_states = rx.synchronize_and_generate_keystream(drive_signal)
print(f"   Receiver states shape: {rx_states.shape}")
print(f"   RX state[0]: x={rx_states[0,0]:.6f}, y={rx_states[0,1]:.6f}, z={rx_states[0,2]:.6f}")
print(f"   RX state[999]: x={rx_states[999,0]:.6f}, y={rx_states[999,1]:.6f}, z={rx_states[999,2]:.6f}")

# Compare states
print("\n3. Comparing states...")
print(f"   X states match (driven): {np.allclose(tx_states[:,0], rx_states[:,0])}")
print(f"   Y states match: {np.allclose(tx_states[:,1], rx_states[:,1], atol=0.01)}")
print(f"   Z states match: {np.allclose(tx_states[:,2], rx_states[:,2], atol=0.01)}")

# Compute errors
error_y = np.abs(tx_states[:,1] - rx_states[:,1])
error_z = np.abs(tx_states[:,2] - rx_states[:,2])
sync_error = np.sqrt(error_y**2 + error_z**2)

print(f"\n4. Synchronization errors:")
print(f"   Mean Y error: {np.mean(error_y):.6f}")
print(f"   Mean Z error: {np.mean(error_z):.6f}")
print(f"   Mean sync error: {np.mean(sync_error):.6f}")
print(f"   Max sync error: {np.max(sync_error):.6f}")
print(f"   Final sync error (last 100): {np.mean(sync_error[-100:]):.6f}")

# Generate keystreams
print("\n5. Comparing keystreams...")
extractor = ChuaKeystreamExtractor()
tx_keystream = extractor.extract(tx_states, enhance=False)
print(f"   TX keystream variance: {np.var(tx_keystream.astype(np.float64)):.2f}")
print(f"   RX keystream variance: {np.var(rx_keystream.astype(np.float64)):.2f}")
print(f"   Keystreams match: {np.array_equal(tx_keystream, rx_keystream)}")
print(f"   Keystream difference: {np.sum(tx_keystream != rx_keystream)} / {len(tx_keystream)}")

# Check first few values
print(f"\n6. First 10 keystream values:")
print(f"   TX: {tx_keystream[:10]}")
print(f"   RX: {rx_keystream[:10]}")
print(f"   Match: {np.array_equal(tx_keystream[:10], rx_keystream[:10])}")

print("\n" + "=" * 80)
if np.array_equal(tx_keystream, rx_keystream):
    print("✓✓✓ KEYSTREAMS MATCH PERFECTLY!")
else:
    print("✗✗✗ KEYSTREAMS DO NOT MATCH")
    print(f"Mismatch rate: {100*np.sum(tx_keystream != rx_keystream)/len(tx_keystream):.2f}%")
print("=" * 80)

# Made with Bob
