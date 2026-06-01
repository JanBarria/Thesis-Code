"""
================================================================================
RÖSSLER SYSTEM KEYSTREAM EXTRACTOR
================================================================================
FPGA Implementation of Chaos-Based Secure Communication
De La Salle University - ECE Thesis Project

AUTHORS: Cortes & Abalos
SYSTEM: Rössler System Keystream Generation

DESCRIPTION:
    This module converts raw chaotic state variables from the Rössler system
    generator into a 16-bit integer keystream suitable for XOR encryption
    with PCM audio samples.
    
    Uses phase-space vector projection method: projects the 3D state vector
    onto a 1D axis to create a high-quality pseudorandom keystream.

METHOD:
    1. Normalize state variables to [-1, 1] range
    2. Project phase-space vector using rotation matrix
    3. Map to 16-bit signed integer range: [-32768, 32767]
    4. Apply bit manipulation for enhanced randomness

HOW TO RUN:
    from rossler_keystream_extractor import RosslerKeystreamExtractor
    
    extractor = RosslerKeystreamExtractor()
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


class RosslerKeystreamExtractor:
    """
    Extract cryptographic keystream from Rössler system state variables
    """
    
    # Normalization bounds (typical Rössler attractor range)
    X_MIN = -10.0
    X_MAX = 10.0
    Y_MIN = -10.0
    Y_MAX = 10.0
    Z_MIN = 0.0
    Z_MAX = 20.0
    
    # Phase-space projection angles (in radians)
    # These angles define the projection direction in 3D space
    THETA = np.pi / 4  # 45 degrees
    PHI = np.pi / 3    # 60 degrees
    
    # 16-bit signed integer range
    INT16_MIN = -32768
    INT16_MAX = 32767
    
    def __init__(self, theta=None, phi=None):
        """
        Initialize keystream extractor
        
        Args:
            theta (float): Optional projection angle theta (radians)
            phi (float): Optional projection angle phi (radians)
        """
        if theta is not None:
            self.theta = theta
        else:
            self.theta = self.THETA
            
        if phi is not None:
            self.phi = phi
        else:
            self.phi = self.PHI
        
        # Compute projection vector
        self._compute_projection_vector()
    
    def _compute_projection_vector(self):
        """
        Compute 3D projection vector from spherical coordinates
        
        The projection vector defines the direction in phase space
        onto which we project the state vector.
        """
        # Convert spherical to Cartesian coordinates
        self.proj_x = np.sin(self.theta) * np.cos(self.phi)
        self.proj_y = np.sin(self.theta) * np.sin(self.phi)
        self.proj_z = np.cos(self.theta)
        
        # Normalize (should already be normalized, but ensure it)
        norm = np.sqrt(self.proj_x**2 + self.proj_y**2 + self.proj_z**2)
        self.proj_x /= norm
        self.proj_y /= norm
        self.proj_z /= norm
    
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
    
    def project_phase_space(self, x_norm, y_norm, z_norm):
        """
        Project 3D phase-space vector onto 1D axis
        
        Uses dot product with projection vector to create 1D signal
        
        Args:
            x_norm (numpy.ndarray): Normalized x state
            y_norm (numpy.ndarray): Normalized y state
            z_norm (numpy.ndarray): Normalized z state
            
        Returns:
            numpy.ndarray: Projected values in approximately [-1, 1] range
        """
        # Dot product: projection = v · p
        # where v = [x, y, z] is state vector
        # and p = [proj_x, proj_y, proj_z] is projection vector
        projected = (x_norm * self.proj_x + 
                    y_norm * self.proj_y + 
                    z_norm * self.proj_z)
        
        # Ensure output is in [-1, 1] (should be due to normalization)
        projected = np.clip(projected, -1.0, 1.0)
        
        return projected
    
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
        
        # Rotate bits left by 5 positions (different from Chua for variety)
        rotated = ((unsigned << 5) | (unsigned >> 11)) & 0xFFFF
        
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
        
        # Project phase space
        projected = self.project_phase_space(x_norm, y_norm, z_norm)
        
        # Map to 16-bit integers
        keystream = self.map_to_int16(projected)
        
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
    Demonstration of Rössler keystream extractor
    """
    print("=" * 80)
    print("RÖSSLER KEYSTREAM EXTRACTOR - DEMONSTRATION")
    print("=" * 80)
    
    # Import generator
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from rossler_chaotic_generator import RosslerGenerator
    
    # Generate chaotic states
    print("\nGenerating chaotic states...")
    generator = RosslerGenerator(x0=0.1, y0=0.0, z0=0.0)
    states = generator.generate(num_samples=10000)
    
    # Create extractor
    print("\nExtracting keystream...")
    extractor = RosslerKeystreamExtractor()
    
    print(f"Projection vector: ({extractor.proj_x:.4f}, {extractor.proj_y:.4f}, {extractor.proj_z:.4f})")
    print(f"Projection angles: theta={extractor.theta:.4f} rad, phi={extractor.phi:.4f} rad")
    
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
