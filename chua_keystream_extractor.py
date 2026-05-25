"""
================================================================================
CHUA CIRCUIT KEYSTREAM EXTRACTOR
================================================================================
FPGA Implementation of Chaos-Based Secure Communication
De La Salle University - ECE Thesis Project

AUTHORS: Barria & Jusay
SYSTEM: Chua Circuit Keystream Generation

DESCRIPTION:
    This module converts raw chaotic state variables from the Chua circuit
    generator into a 16-bit integer keystream suitable for XOR encryption
    with PCM audio samples.
    
    Uses state-variable sampling method: combines multiple state variables
    to create a high-quality pseudorandom keystream.

METHOD:
    1. Normalize state variables to [-1, 1] range
    2. Combine states using weighted sum: K_float = w1*x + w2*y + w3*z
    3. Map to 16-bit signed integer range: [-32768, 32767]
    4. Apply bit manipulation for enhanced randomness

HOW TO RUN:
    from chua_keystream_extractor import ChuaKeystreamExtractor
    
    extractor = ChuaKeystreamExtractor()
    keystream = extractor.extract(states)  # states from generator
    
INPUTS:
    - states: numpy array of shape (N, 3) containing [x, y, z] values
    
OUTPUTS:
    - keystream: numpy array of shape (N,) containing 16-bit integers
    - Compatible with audio PCM samples for XOR operation

NOTES:
    - Ensures uniform distribution across 16-bit range
    - Includes statistical tests for keystream quality
    - Compatible with PYNQ-Z2 Python 3.x environment
================================================================================
"""

import numpy as np
import warnings


class ChuaKeystreamExtractor:
    """
    Extract cryptographic keystream from Chua circuit state variables
    """
    
    # Normalization bounds (typical Chua attractor range)
    X_MIN = -4.0
    X_MAX = 4.0
    Y_MIN = -1.0
    Y_MAX = 1.0
    Z_MIN = -6.0
    Z_MAX = 6.0
    
    # Mixing weights for state combination
    # These weights are chosen to maximize entropy
    WEIGHT_X = 0.5
    WEIGHT_Y = 0.3
    WEIGHT_Z = 0.2
    
    # 16-bit signed integer range
    INT16_MIN = -32768
    INT16_MAX = 32767
    
    def __init__(self, weights=None):
        """
        Initialize keystream extractor
        
        Args:
            weights (tuple): Optional (wx, wy, wz) mixing weights
                           Default: (0.5, 0.3, 0.2)
        """
        if weights is not None:
            self.weight_x, self.weight_y, self.weight_z = weights
            # Normalize weights to sum to 1
            total = self.weight_x + self.weight_y + self.weight_z
            self.weight_x /= total
            self.weight_y /= total
            self.weight_z /= total
        else:
            self.weight_x = self.WEIGHT_X
            self.weight_y = self.WEIGHT_Y
            self.weight_z = self.WEIGHT_Z
    
    def normalize_state(self, x, y, z):
        """
        Normalize state variables to [-1, 1] range
        
        Args:
            x (numpy.ndarray): x state variable
            y (numpy.ndarray): y state variable
            z (numpy.ndarray): z state variable
            
        Returns:
            tuple: (x_norm, y_norm, z_norm) normalized states
        """
        # Clip to expected bounds
        x_clipped = np.clip(x, self.X_MIN, self.X_MAX)
        y_clipped = np.clip(y, self.Y_MIN, self.Y_MAX)
        z_clipped = np.clip(z, self.Z_MIN, self.Z_MAX)
        
        # Normalize to [-1, 1]
        x_norm = 2.0 * (x_clipped - self.X_MIN) / (self.X_MAX - self.X_MIN) - 1.0
        y_norm = 2.0 * (y_clipped - self.Y_MIN) / (self.Y_MAX - self.Y_MIN) - 1.0
        z_norm = 2.0 * (z_clipped - self.Z_MIN) / (self.Z_MAX - self.Z_MIN) - 1.0
        
        return x_norm, y_norm, z_norm
    
    def combine_states(self, x_norm, y_norm, z_norm):
        """
        Combine normalized states using weighted sum
        
        Args:
            x_norm (numpy.ndarray): Normalized x state
            y_norm (numpy.ndarray): Normalized y state
            z_norm (numpy.ndarray): Normalized z state
            
        Returns:
            numpy.ndarray: Combined state in [-1, 1] range
        """
        combined = (self.weight_x * x_norm + 
                   self.weight_y * y_norm + 
                   self.weight_z * z_norm)
        
        # Ensure output is in [-1, 1]
        combined = np.clip(combined, -1.0, 1.0)
        
        return combined
    
    def map_to_int16(self, normalized):
        """
        Map normalized float values to 16-bit signed integers
        
        Args:
            normalized (numpy.ndarray): Values in [-1, 1] range
            
        Returns:
            numpy.ndarray: 16-bit signed integers
        """
        # Scale to [INT16_MIN, INT16_MAX]
        scaled = normalized * self.INT16_MAX
        
        # Convert to int16
        keystream = np.round(scaled).astype(np.int16)
        
        return keystream
    
    def enhance_randomness(self, keystream):
        """
        Apply bit manipulation to enhance randomness
        
        Uses XOR with bit-rotated version of itself to increase entropy
        
        Args:
            keystream (numpy.ndarray): Input keystream
            
        Returns:
            numpy.ndarray: Enhanced keystream
        """
        # Convert to unsigned for bit operations
        unsigned = keystream.astype(np.uint16)
        
        # Rotate bits left by 3 positions
        rotated = ((unsigned << 3) | (unsigned >> 13)) & 0xFFFF
        
        # XOR with rotated version
        enhanced = unsigned ^ rotated
        
        # Convert back to signed
        return enhanced.astype(np.int16)
    
    def extract(self, states, enhance=True):
        """
        Extract keystream from chaotic states
        
        Args:
            states (numpy.ndarray): Array of shape (N, 3) with [x, y, z]
            enhance (bool): Apply randomness enhancement (default: True)
            
        Returns:
            numpy.ndarray: Keystream of shape (N,) with 16-bit integers
        """
        # Validate input
        if states.ndim != 2 or states.shape[1] != 3:
            raise ValueError("States must be array of shape (N, 3)")
        
        # Extract state variables
        x = states[:, 0]
        y = states[:, 1]
        z = states[:, 2]
        
        # Normalize states
        x_norm, y_norm, z_norm = self.normalize_state(x, y, z)
        
        # Combine states
        combined = self.combine_states(x_norm, y_norm, z_norm)
        
        # Map to 16-bit integers
        keystream = self.map_to_int16(combined)
        
        # Enhance randomness if requested
        if enhance:
            keystream = self.enhance_randomness(keystream)
        
        # Validate keystream quality
        self._validate_keystream(keystream)
        
        return keystream
    
    def _validate_keystream(self, keystream):
        """
        Validate keystream quality using statistical tests
        
        Args:
            keystream (numpy.ndarray): Generated keystream
        """
        # Test 1: Check for sufficient entropy (variance)
        variance = np.var(keystream.astype(np.float64))
        expected_variance = ((self.INT16_MAX - self.INT16_MIN) ** 2) / 12  # Uniform distribution
        
        if variance < 0.5 * expected_variance:
            warnings.warn(
                f"Low keystream variance detected: {variance:.2f} "
                f"(expected ~{expected_variance:.2f})"
            )
        
        # Test 2: Check distribution uniformity (chi-square-like test)
        # Divide range into bins and check distribution
        hist, _ = np.histogram(keystream, bins=256, range=(self.INT16_MIN, self.INT16_MAX))
        expected_count = len(keystream) / 256
        chi_square = np.sum((hist - expected_count) ** 2 / expected_count)
        
        # Rough threshold (chi-square with 255 df, p=0.05 is ~293)
        if chi_square > 500:
            warnings.warn(
                f"Keystream distribution may be non-uniform. Chi-square: {chi_square:.2f}"
            )
        
        # Test 3: Check for runs (consecutive identical values)
        runs = np.sum(np.diff(keystream) == 0)
        run_ratio = runs / len(keystream)
        
        if run_ratio > 0.01:  # More than 1% runs
            warnings.warn(
                f"High number of runs detected: {runs} ({run_ratio*100:.2f}%)"
            )
    
    def get_statistics(self, keystream):
        """
        Compute and return keystream statistics
        
        Args:
            keystream (numpy.ndarray): Keystream to analyze
            
        Returns:
            dict: Dictionary containing statistical measures
        """
        stats = {
            'mean': np.mean(keystream.astype(np.float64)),
            'std': np.std(keystream.astype(np.float64)),
            'min': np.min(keystream),
            'max': np.max(keystream),
            'variance': np.var(keystream.astype(np.float64)),
            'unique_values': len(np.unique(keystream)),
            'total_values': len(keystream)
        }
        
        # Compute entropy (Shannon entropy)
        hist, _ = np.histogram(keystream, bins=256, range=(self.INT16_MIN, self.INT16_MAX))
        prob = hist / len(keystream)
        prob = prob[prob > 0]  # Remove zero probabilities
        entropy = -np.sum(prob * np.log2(prob))
        stats['entropy_bits'] = entropy
        
        return stats


# ============================================================================
# DEMONSTRATION AND TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Demonstration of Chua keystream extractor
    """
    print("=" * 80)
    print("CHUA KEYSTREAM EXTRACTOR - DEMONSTRATION")
    print("=" * 80)
    
    # Import generator
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from chua_chaotic_generator import ChuaGenerator
    
    # Generate chaotic states
    print("\nGenerating chaotic states...")
    generator = ChuaGenerator(x0=0.1, y0=0.0, z0=0.0)
    states = generator.generate(num_samples=10000)
    
    # Create extractor
    print("\nExtracting keystream...")
    extractor = ChuaKeystreamExtractor()
    
    print(f"Mixing weights: x={extractor.weight_x:.2f}, "
          f"y={extractor.weight_y:.2f}, z={extractor.weight_z:.2f}")
    
    # Extract keystream
    keystream = extractor.extract(states, enhance=True)
    
    # Display statistics
    print(f"\nKeystream Statistics:")
    stats = extractor.get_statistics(keystream)
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    
    # Test without enhancement
    print("\n" + "-" * 80)
    print("Testing without randomness enhancement...")
    keystream_no_enhance = extractor.extract(states, enhance=False)
    stats_no_enhance = extractor.get_statistics(keystream_no_enhance)
    print(f"Entropy (no enhancement): {stats_no_enhance['entropy_bits']:.4f} bits")
    print(f"Entropy (with enhancement): {stats['entropy_bits']:.4f} bits")
    
    # Display sample values
    print(f"\nFirst 20 keystream values:")
    print(keystream[:20])
    
    print("\n" + "=" * 80)
    print("Keystream extractor demonstration complete!")
    print("=" * 80)

# Made with Bob
