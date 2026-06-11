#!/usr/bin/env python3
"""
================================================================================
Chaotic Attractor Visualization Script - Phase 2 Verification
================================================================================
Author: Senior Digital Design and FPGA Verification Engineer
Purpose: Functional verification of FPGA-synthesized chaotic oscillators
         via phase portrait reconstruction from hardware simulation data

This script implements Deliverable 2 of Specific Objective 2 (SO2):
"Functional Verification via Attractor Reconstruction"

Input File Format:
    - File: 'chaotic_hardware_vectors.txt'
    - Format: Space-separated hexadecimal values per line
    - Structure: rossler_x rossler_y rossler_z chua_x chua_y chua_z
    - Example: fffa83a2 0006c6ed 000004e5 00000000 00000000 00000000

Fixed-Point Encoding:
    - Format: Q16.16 (16-bit integer, 16-bit fractional)
    - Total bits: 32 (signed)
    - Conversion: float_value = signed_int_value / 65536
    - Range: -32768.0 to +32767.99998
    - Resolution: 1/65536 ≈ 0.000015

Mathematical Background:
    Two's complement representation for negative numbers:
    - If MSB = 1, number is negative
    - Python's int(hex_string, 16) treats as unsigned
    - Must convert: if value > 2^31-1, then value -= 2^32
    
    Example: 'fffa83a2'
    - Unsigned interpretation: 4,293,829,538
    - Signed interpretation: -1,937,758 (correct)
    - Float value: -1,937,758 / 65536 = -29.57 (correct)

Dependencies:
    - numpy: Numerical array operations
    - matplotlib: 2D/3D plotting
    
Usage:
    python visualize_attractors.py
    
Output:
    - Console: Data range statistics for thesis tables
    - Figures: 2D phase portraits (X vs Y) for both oscillators
    - Optional: 3D phase portraits (X vs Y vs Z)
================================================================================
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ==============================================================================
# CONFIGURATION PARAMETERS
# ==============================================================================

# Input file paths (relative to script location)
ROSSLER_FILE = 'rossler_hardware_vectors.txt'
CHUA_FILE = 'chua_hardware_vectors.txt'

# Q16.16 fixed-point scaling factor
# Hardware multiplies floats by 65536 to convert to integers
# We divide by 65536 to convert back to floats
FIXED_POINT_SCALE = 65536

# Two's complement bit width (32-bit signed integers)
BIT_WIDTH = 32
MAX_UNSIGNED = 2**BIT_WIDTH  # 4,294,967,296
SIGN_BIT_THRESHOLD = 2**(BIT_WIDTH - 1)  # 2,147,483,648

# Plotting configuration
PLOT_STYLE = 'seaborn-v0_8-darkgrid'  # Modern matplotlib style
FIGURE_DPI = 150  # High resolution for thesis figures
POINT_SIZE = 1  # Small points for dense trajectories (must be int)
POINT_ALPHA = 0.6  # Transparency for overlapping points

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def hex_to_signed_int(hex_string):
    """
    Convert 32-bit hexadecimal string to signed integer using two's complement.
    
    Two's complement conversion:
    1. Parse hex string as unsigned integer
    2. If value >= 2^31 (MSB = 1), it's negative
    3. Convert: signed_value = unsigned_value - 2^32
    
    Args:
        hex_string (str): 8-character hexadecimal string (e.g., 'fffa83a2')
    
    Returns:
        int: Signed integer value
    
    Example:
        hex_to_signed_int('fffa83a2') → -1,937,758
        hex_to_signed_int('0006c6ed') → 444,141
        hex_to_signed_int('00010000') → 65,536 (represents 1.0 in Q16.16)
    """
    # Parse hexadecimal string as unsigned integer
    unsigned_value = int(hex_string, 16)
    
    # Check if MSB is set (negative number in two's complement)
    if unsigned_value >= SIGN_BIT_THRESHOLD:
        # Convert to signed by subtracting 2^32
        signed_value = unsigned_value - MAX_UNSIGNED
    else:
        # Positive number, no conversion needed
        signed_value = unsigned_value
    
    return signed_value


def fixed_point_to_float(signed_int):
    """
    Convert Q16.16 fixed-point integer to floating-point decimal.
    
    Q16.16 format:
    - 16 bits for integer part (including sign)
    - 16 bits for fractional part
    - Division by 65536 (2^16) shifts decimal point 16 places right
    
    Args:
        signed_int (int): Signed integer in Q16.16 format
    
    Returns:
        float: Floating-point value
    
    Example:
        fixed_point_to_float(65536) → 1.0
        fixed_point_to_float(-1937758) → -29.57
        fixed_point_to_float(6554) → 0.1
    """
    return signed_int / FIXED_POINT_SCALE


def parse_hardware_vector_line(line):
    """
    Parse a single line from the hardware output file.
    
    Expected format: "x y z" (three space-separated hex values)
    All values are 32-bit hexadecimal strings (8 characters each).
    
    Args:
        line (str): Single line from input file
    
    Returns:
        tuple: (x, y, z) as floats after conversion
    
    Raises:
        ValueError: If line doesn't contain exactly 3 hex values
    """
    # Split line by whitespace and remove empty strings
    hex_values = line.strip().split()
    
    # Validate format
    if len(hex_values) != 3:
        raise ValueError(f"Expected 3 hex values, got {len(hex_values)}: {line}")
    
    # Convert each hex value: hex → signed int → float
    float_values = []
    for hex_val in hex_values:
        signed_int = hex_to_signed_int(hex_val)
        float_val = fixed_point_to_float(signed_int)
        float_values.append(float_val)
    
    return tuple(float_values)


def load_single_oscillator_data(filename):
    """
    Load and parse a single oscillator's hardware simulation output file.
    
    Reads the file line-by-line, converts hex values to floats.
    
    Args:
        filename (str): Path to input file
    
    Returns:
        numpy.ndarray: Array of shape (N, 3) where N is sample count
                       Columns are [X, Y, Z]
    
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If file contains invalid data
    """
    # Check if file exists
    file_path = Path(filename)
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {filename}")
    
    # Initialize list to store parsed data
    data = []
    
    # Read and parse file line by line
    print(f"Reading hardware data from: {filename}")
    with open(filename, 'r') as f:
        for line_num, line in enumerate(f, start=1):
            # Skip empty lines
            if not line.strip():
                continue
            
            try:
                # Parse line: returns (x, y, z)
                x, y, z = parse_hardware_vector_line(line)
                
                # Append to list
                data.append([x, y, z])
                
            except ValueError as e:
                print(f"Warning: Skipping invalid line {line_num}: {e}")
                continue
    
    # Convert list to numpy array for efficient computation
    data_array = np.array(data)
    
    print(f"Successfully loaded {len(data_array)} samples")
    print(f"Data shape: {data_array.shape}")
    
    return data_array


def load_hardware_data(rossler_file, chua_file):
    """
    Load and parse both oscillators' hardware simulation output files.
    
    Args:
        rossler_file (str): Path to Rössler output file
        chua_file (str): Path to Chua output file
    
    Returns:
        tuple: (rossler_data, chua_data)
               Each is a numpy array of shape (N, 3) where N is sample count
               Columns are [X, Y, Z] for each oscillator
    
    Raises:
        FileNotFoundError: If either input file doesn't exist
    """
    print("Loading Rössler oscillator data...")
    rossler_data = load_single_oscillator_data(rossler_file)
    
    print("\nLoading Chua oscillator data...")
    chua_data = load_single_oscillator_data(chua_file)
    
    return rossler_data, chua_data


def compute_statistics(data, name):
    """
    Compute and print statistical summary of oscillator data.
    
    Calculates min, max, mean, and standard deviation for X, Y, Z states.
    This data is essential for thesis summary tables.
    
    Args:
        data (numpy.ndarray): Array of shape (N, 3) with columns [X, Y, Z]
        name (str): Oscillator name for display (e.g., "Rössler")
    """
    print(f"\n{'='*70}")
    print(f"{name} Oscillator - Statistical Summary")
    print(f"{'='*70}")
    print(f"{'State':<10} {'Min':>12} {'Max':>12} {'Mean':>12} {'Std Dev':>12}")
    print(f"{'-'*70}")
    
    state_names = ['X', 'Y', 'Z']
    for i, state in enumerate(state_names):
        col_data = data[:, i]
        print(f"{state:<10} {np.min(col_data):>12.6f} {np.max(col_data):>12.6f} "
              f"{np.mean(col_data):>12.6f} {np.std(col_data):>12.6f}")
    
    print(f"{'='*70}\n")


def plot_2d_phase_portrait(data, title, filename, color='blue'):
    """
    Create 2D phase portrait (X vs Y projection).
    
    Phase portraits visualize the system's trajectory in state space.
    For chaotic systems, the trajectory fills a strange attractor with
    fractal structure, confirming chaotic behavior.
    
    Args:
        data (numpy.ndarray): Array of shape (N, 3) with columns [X, Y, Z]
        title (str): Plot title
        filename (str): Output filename for saving figure
        color (str): Plot color
    """
    plt.figure(figsize=(10, 8), dpi=FIGURE_DPI)
    
    # Extract X and Y columns
    x_data = data[:, 0]
    y_data = data[:, 1]
    
    # Create scatter plot with small, semi-transparent points
    plt.scatter(x_data, y_data, s=POINT_SIZE, alpha=POINT_ALPHA, 
                c=color, edgecolors='none')
    
    # Formatting
    plt.xlabel('X State', fontsize=12, fontweight='bold')
    plt.ylabel('Y State', fontsize=12, fontweight='bold')
    plt.title(title, fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save figure
    plt.savefig(filename, dpi=FIGURE_DPI, bbox_inches='tight')
    print(f"Saved 2D phase portrait: {filename}")
    
    # Display
    plt.show()


def plot_3d_phase_portrait(data, title, filename, color='blue'):
    """
    Create 3D phase portrait (X vs Y vs Z).
    
    3D visualization shows the full attractor structure in state space.
    Optional but provides better insight into chaotic dynamics.
    
    Args:
        data (numpy.ndarray): Array of shape (N, 3) with columns [X, Y, Z]
        title (str): Plot title
        filename (str): Output filename for saving figure
        color (str): Plot color
    """
    from mpl_toolkits.mplot3d import Axes3D
    
    fig = plt.figure(figsize=(12, 10), dpi=FIGURE_DPI)
    ax = fig.add_subplot(111, projection='3d')
    
    # Extract X, Y, Z columns
    x_data = data[:, 0]
    y_data = data[:, 1]
    z_data = data[:, 2]
    
    # Create 3D scatter plot
    ax.scatter(x_data, y_data, z_data, s=POINT_SIZE, alpha=POINT_ALPHA,
               c=color, edgecolors='none')
    
    # Formatting
    ax.set_xlabel('X State', fontsize=12, fontweight='bold')
    ax.set_ylabel('Y State', fontsize=12, fontweight='bold')
    ax.set_zlabel('Z State', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Save figure
    plt.tight_layout()
    plt.savefig(filename, dpi=FIGURE_DPI, bbox_inches='tight')
    print(f"Saved 3D phase portrait: {filename}")
    
    # Display
    plt.show()


# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

def main():
    """
    Main execution function for Phase 2 verification.
    
    Workflow:
    1. Load hardware simulation data
    2. Compute and display statistics
    3. Generate 2D phase portraits
    4. Optionally generate 3D phase portraits
    """
    print("="*70)
    print("PHASE 2: Chaotic Attractor Reconstruction and Verification")
    print("="*70)
    
    try:
        # Step 1: Load and parse hardware data
        rossler_data, chua_data = load_hardware_data(ROSSLER_FILE, CHUA_FILE)
        
        # Step 2: Compute statistics for thesis tables
        compute_statistics(rossler_data, "Rössler")
        compute_statistics(chua_data, "Chua")
        
        # Step 3: Generate 2D phase portraits (X vs Y)
        print("\nGenerating 2D phase portraits...")
        plot_2d_phase_portrait(
            rossler_data,
            "Rössler Attractor - 2D Phase Portrait (X vs Y)",
            "rossler_2d_phase_portrait.png",
            color='darkblue'
        )
        
        plot_2d_phase_portrait(
            chua_data,
            "Chua Attractor - 2D Phase Portrait (X vs Y)",
            "chua_2d_phase_portrait.png",
            color='darkred'
        )
        
        # Step 4: Generate 3D phase portraits (optional)
        print("\nGenerating 3D phase portraits...")
        user_input = input("Generate 3D plots? (y/n): ").strip().lower()
        
        if user_input == 'y':
            plot_3d_phase_portrait(
                rossler_data,
                "Rössler Attractor - 3D Phase Portrait",
                "rossler_3d_phase_portrait.png",
                color='darkblue'
            )
            
            plot_3d_phase_portrait(
                chua_data,
                "Chua Attractor - 3D Phase Portrait",
                "chua_3d_phase_portrait.png",
                color='darkred'
            )
        
        print("\n" + "="*70)
        print("Phase 2 Verification Complete!")
        print("="*70)
        print("\nGenerated files:")
        print("  - rossler_2d_phase_portrait.png")
        print("  - chua_2d_phase_portrait.png")
        if user_input == 'y':
            print("  - rossler_3d_phase_portrait.png")
            print("  - chua_3d_phase_portrait.png")
        print("\nStatistical data printed above for thesis tables.")
        print("="*70)
        
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("Please ensure these files are in the same directory:")
        print(f"  - {ROSSLER_FILE}")
        print(f"  - {CHUA_FILE}")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Set matplotlib style for professional plots
    try:
        plt.style.use(PLOT_STYLE)
    except:
        print(f"Warning: Style '{PLOT_STYLE}' not available, using default")
    
    # Run main verification workflow
    main()

# Made with Bob
