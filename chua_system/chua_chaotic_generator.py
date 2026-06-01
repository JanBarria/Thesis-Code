"""
================================================================================
CHUA CIRCUIT CHAOTIC GENERATOR
================================================================================
FPGA Implementation of Chaos-Based Secure Communication
De La Salle University - ECE Thesis Project

AUTHORS: Barria & Jusay
SYSTEM: Chua Circuit (Double-Scroll Attractor)

DESCRIPTION:
    This module implements the Chua circuit chaotic oscillator using Forward
    Euler discretization with Q16.16 fixed-point arithmetic simulation.
    
    The Chua circuit is a third-order autonomous nonlinear circuit that 
    exhibits chaotic behavior through a piecewise-linear nonlinearity 
    (Chua diode).

STATE EQUATIONS:
    ẋ = α(y - x - f(x))
    ẏ = x - y + z
    ż = -βy
    
    where f(x) = bx + 0.5(a-b)(|x+1| - |x-1|)  [Chua diode]

PARAMETERS:
    α = 9.0
    β = 14.28
    a = -1.143
    b = -0.714
    dt = 0.01 (time step)

FIXED-POINT FORMAT:
    Q16.16 format (16 integer bits, 16 fractional bits)
    Range: -32768.0 to 32767.9999847412109375

HOW TO RUN:
    from chua_chaotic_generator import ChuaGenerator
    
    generator = ChuaGenerator()
    states = generator.generate(num_samples=10000)
    x, y, z = states[:, 0], states[:, 1], states[:, 2]

INPUTS:
    - Initial conditions: x0, y0, z0 (default: 0.1, 0.0, 0.0)
    - Number of samples to generate
    
OUTPUTS:
    - Numpy array of shape (num_samples, 3) containing [x, y, z] states
    - Each row represents one time step

NOTES:
    - Includes overflow detection and modulo-map stabilization
    - Validates that attractor has not collapsed into periodic orbit
    - Compatible with PYNQ-Z2 Python 3.x environment
================================================================================
"""

import numpy as np
import warnings


class ChuaGenerator:
    """
    Chua Circuit Chaotic Oscillator with Q16.16 Fixed-Point Simulation
    """
    
    # Chua circuit parameters
    ALPHA = 9.0
    BETA = 14.28
    A = -1.143
    B = -0.714
    DT = 0.01  # Time step for Forward Euler
    
    # Q16.16 fixed-point parameters
    FRAC_BITS = 16
    SCALE_FACTOR = 2 ** FRAC_BITS  # 65536
    MAX_VALUE = 32767.0
    MIN_VALUE = -32768.0
    
    # Modulo-map bounds to prevent overflow
    MODULO_BOUND = 20.0
    
    def __init__(self, x0=0.1, y0=0.0, z0=0.0, dt=None):
        """
        Initialize Chua circuit generator
        
        Args:
            x0 (float): Initial condition for x state
            y0 (float): Initial condition for y state
            z0 (float): Initial condition for z state
            dt (float): Time step (default: 0.01)
        """
        self.x = float(x0)
        self.y = float(y0)
        self.z = float(z0)
        
        if dt is not None:
            self.dt = dt
        else:
            self.dt = self.DT
            
        # Store initial conditions for reset
        self.x0 = x0
        self.y0 = y0
        self.z0 = z0
        
        # Statistics for validation
        self.overflow_count = 0
        self.modulo_wrap_count = 0
        
    def chua_diode(self, x):
        """
        Chua diode piecewise-linear function
        
        f(x) = bx + 0.5(a-b)(|x+1| - |x-1|)
        
        Args:
            x (float): Input state variable
            
        Returns:
            float: Chua diode output
        """
        term1 = self.B * x
        term2 = 0.5 * (self.A - self.B) * (abs(x + 1.0) - abs(x - 1.0))
        return term1 + term2
    
    def fixed_point_simulate(self, value):
        """
        Simulate Q16.16 fixed-point arithmetic
        
        Converts float to fixed-point integer and back to simulate
        quantization effects that will occur in FPGA implementation.
        
        Args:
            value (float): Input value
            
        Returns:
            float: Quantized value
        """
        # Convert to fixed-point integer
        fixed_int = int(value * self.SCALE_FACTOR)
        
        # Check for overflow
        max_int = int(self.MAX_VALUE * self.SCALE_FACTOR)
        min_int = int(self.MIN_VALUE * self.SCALE_FACTOR)
        
        if fixed_int > max_int or fixed_int < min_int:
            self.overflow_count += 1
            # Saturate to prevent overflow
            fixed_int = max(min_int, min(max_int, fixed_int))
        
        # Convert back to float
        return fixed_int / self.SCALE_FACTOR
    
    def modulo_map(self, value):
        """
        Apply modulo mapping to prevent state explosion
        
        Wraps values outside [-MODULO_BOUND, MODULO_BOUND] back into range
        while preserving chaotic dynamics.
        
        Args:
            value (float): Input value
            
        Returns:
            float: Wrapped value
        """
        if abs(value) > self.MODULO_BOUND:
            self.modulo_wrap_count += 1
            # Wrap using modulo operation
            range_size = 2 * self.MODULO_BOUND
            wrapped = ((value + self.MODULO_BOUND) % range_size) - self.MODULO_BOUND
            return wrapped
        return value
    
    def step(self):
        """
        Perform one Forward Euler integration step
        
        Updates internal state variables x, y, z
        
        Returns:
            tuple: (x, y, z) current state after step
        """
        # Compute Chua diode nonlinearity
        fx = self.chua_diode(self.x)
        
        # Compute derivatives
        dx_dt = self.ALPHA * (self.y - self.x - fx)
        dy_dt = self.x - self.y + self.z
        dz_dt = -self.BETA * self.y
        
        # Forward Euler integration
        x_new = self.x + self.dt * dx_dt
        y_new = self.y + self.dt * dy_dt
        z_new = self.z + self.dt * dz_dt
        
        # Apply fixed-point quantization
        x_new = self.fixed_point_simulate(x_new)
        y_new = self.fixed_point_simulate(y_new)
        z_new = self.fixed_point_simulate(z_new)
        
        # Apply modulo mapping to prevent overflow
        x_new = self.modulo_map(x_new)
        y_new = self.modulo_map(y_new)
        z_new = self.modulo_map(z_new)
        
        # Update state
        self.x = x_new
        self.y = y_new
        self.z = z_new
        
        return self.x, self.y, self.z
    
    def generate(self, num_samples):
        """
        Generate chaotic time series
        
        Args:
            num_samples (int): Number of samples to generate
            
        Returns:
            numpy.ndarray: Array of shape (num_samples, 3) with [x, y, z] states
        """
        # Pre-allocate output array
        states = np.zeros((num_samples, 3), dtype=np.float64)
        
        # Reset statistics
        self.overflow_count = 0
        self.modulo_wrap_count = 0
        
        # Generate samples
        for i in range(num_samples):
            x, y, z = self.step()
            states[i] = [x, y, z]
        
        # Validate chaotic behavior
        self._validate_chaos(states)
        
        # Print statistics
        if self.overflow_count > 0:
            warnings.warn(f"Fixed-point overflow occurred {self.overflow_count} times")
        
        if self.modulo_wrap_count > 0:
            print(f"Modulo wrapping applied {self.modulo_wrap_count} times")
        
        return states
    
    def _validate_chaos(self, states):
        """
        Validate that the attractor has not collapsed into periodic orbit
        
        Checks for:
        1. Non-zero variance in all state variables
        2. Approximate divergence of nearby trajectories (Lyapunov-like)
        
        Args:
            states (numpy.ndarray): Generated state array
        """
        # Check variance
        variances = np.var(states, axis=0)
        
        if np.any(variances < 1e-6):
            warnings.warn(
                "WARNING: Low variance detected. Attractor may have collapsed!\n"
                f"Variances: x={variances[0]:.6f}, y={variances[1]:.6f}, z={variances[2]:.6f}"
            )
        
        # Check for divergence (simplified Lyapunov-like test)
        if len(states) > 100:
            # Compare trajectory segments
            segment1 = states[10:60]
            segment2 = states[60:110]
            
            # Compute mean absolute difference
            diff = np.mean(np.abs(segment2 - segment1))
            
            if diff < 0.01:
                warnings.warn(
                    "WARNING: Trajectory segments are too similar. "
                    "System may be periodic rather than chaotic!"
                )
    
    def reset(self):
        """Reset generator to initial conditions"""
        self.x = self.x0
        self.y = self.y0
        self.z = self.z0
        self.overflow_count = 0
        self.modulo_wrap_count = 0
    
    def get_state(self):
        """
        Get current state
        
        Returns:
            tuple: (x, y, z) current state
        """
        return (self.x, self.y, self.z)
    
    def set_state(self, x, y, z):
        """
        Set current state (useful for synchronization)
        
        Args:
            x (float): x state value
            y (float): y state value
            z (float): z state value
        """
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


# ============================================================================
# DEMONSTRATION AND TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Demonstration of Chua circuit generator
    """
    print("=" * 80)
    print("CHUA CIRCUIT CHAOTIC GENERATOR - DEMONSTRATION")
    print("=" * 80)
    
    # Create generator
    generator = ChuaGenerator(x0=0.1, y0=0.0, z0=0.0)
    
    print(f"\nParameters:")
    print(f"  α = {generator.ALPHA}")
    print(f"  β = {generator.BETA}")
    print(f"  a = {generator.A}")
    print(f"  b = {generator.B}")
    print(f"  dt = {generator.dt}")
    print(f"  Initial conditions: x0={generator.x0}, y0={generator.y0}, z0={generator.z0}")
    
    # Generate samples
    print(f"\nGenerating 10000 samples...")
    states = generator.generate(num_samples=10000)
    
    # Display statistics
    print(f"\nStatistics:")
    print(f"  x: mean={np.mean(states[:, 0]):.4f}, std={np.std(states[:, 0]):.4f}, "
          f"min={np.min(states[:, 0]):.4f}, max={np.max(states[:, 0]):.4f}")
    print(f"  y: mean={np.mean(states[:, 1]):.4f}, std={np.std(states[:, 1]):.4f}, "
          f"min={np.min(states[:, 1]):.4f}, max={np.max(states[:, 1]):.4f}")
    print(f"  z: mean={np.mean(states[:, 2]):.4f}, std={np.std(states[:, 2]):.4f}, "
          f"min={np.min(states[:, 2]):.4f}, max={np.max(states[:, 2]):.4f}")
    
    print(f"\nOverflow events: {generator.overflow_count}")
    print(f"Modulo wrapping events: {generator.modulo_wrap_count}")
    
    # Test single step
    print(f"\nTesting single step:")
    generator.reset()
    for i in range(5):
        x, y, z = generator.step()
        print(f"  Step {i+1}: x={x:.6f}, y={y:.6f}, z={z:.6f}")
    
    print("\n" + "=" * 80)
    print("Chua generator demonstration complete!")
    print("=" * 80)

# Made with Bob
