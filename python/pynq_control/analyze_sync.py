#!/usr/bin/env python3
"""
Laptop-side Analysis and Plotting Script for Hybrid Single-Board Chaos Data.
Parses a unified hybrid_data.csv file to analyze synchronization states.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Update this path to match exactly where you saved the file on your laptop
DATA_FILE = "C:/thesis/hybrid_data.csv"

def main():
    print("====================================================================")
    print("               CHAOS SYNCHRONIZATION ANALYSIS (HYBRID)              ")
    print("====================================================================")
    
    if not os.path.exists(DATA_FILE):
        print(f"Error: Data file not found at {DATA_FILE}")
        print("Please verify the file path location on your laptop.")
        return

    print(f"Loading data file: {DATA_FILE}...")
    df = pd.read_csv(DATA_FILE)
    
    # Extract time vector
    t = df['t'].values
    
    # 1. Extract Chua Circuit State Matrices
    mc_x, sc_x = df['mc_x'].values, df['sc_x'].values
    mc_y, sc_y = df['mc_y'].values, df['sc_y'].values
    mc_z, sc_z = df['mc_z'].values, df['sc_z'].values
    
    # 2. Extract Rössler Circuit State Matrices
    mr_x, sr_x = df['mr_x'].values, df['sr_x'].values
    mr_y, sr_y = df['mr_y'].values, df['sr_y'].values
    mr_z       = df['mr_z'].values  # sr_z is omitted in hardware map layout
    
    # Calculate Synchronization Errors over time
    chua_error = np.abs(mc_x - sc_x)
    rossler_error = np.abs(mr_x - sr_x)
    
    print("\nProcessing Synchronization Metrics...")
    print(f"Chua Mean Absolute Error (X):    {np.mean(chua_error):.5f}")
    print(f"Rössler Mean Absolute Error (X): {np.mean(rossler_error):.5f}")

    # ====================================================================
    # PLOT 1: TIME-SERIES TRAJECTORY SYNC
    # ====================================================================
    plt.figure(figsize=(12, 5))
    plt.plot(t, mc_x, label="Master Chua (mc_x)", color='blue', alpha=0.8)
    plt.plot(t, sc_x, label="Slave Chua (sc_x)", color='orange', linestyle='--', alpha=0.8)
    plt.title("Chua Circuit State Synchronization Trajectory Over Time")
    plt.xlabel("Time (s)")
    plt.ylabel("State Amplitude")
    plt.legend(loc="upper right")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("C:/thesis/chua_time_sync.png", dpi=300)
    
    # ====================================================================
    # PLOT 2: SYNCHRONIZATION MANIFOLD (ATTRACTOR COLLAPSE)
    # ====================================================================
    plt.figure(figsize=(6, 6))
    plt.scatter(mc_x, sc_x, s=1, color='purple', alpha=0.5)
    
    # Generate the ideal reference diagonal line (Y = X)
    lims = [np.min([mc_x, sc_x]), np.max([mc_x, sc_x])]
    plt.plot(lims, lims, 'r-', alpha=0.7, label="Ideal Sync (Y=X)")
    
    plt.title("Chua Synchronization Manifold Attractor Plot")
    plt.xlabel("Master State (mc_x)")
    plt.ylabel("Slave State (sc_x)")
    plt.legend(loc="upper left")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("C:/thesis/chua_manifold_sync.png", dpi=300)
    
    # ====================================================================
    # PLOT 3: ERROR CONVERGENCE TIMELINE
    # ====================================================================
    plt.figure(figsize=(12, 4))
    plt.plot(t, chua_error, color='red', alpha=0.8, label="Error |mc_x - sc_x|")
    plt.title("Chua Synchronization Convergence Error Decay Rate")
    plt.xlabel("Time (s)")
    plt.ylabel("Absolute Error Magnitude")
    plt.legend(loc="upper right")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("C:/thesis/chua_error_convergence.png", dpi=300)
    
    print("\nSUCCESS: Analysis complete! Generated plots have been saved to your local folder:")
    print(" -> C:/thesis/chua_time_sync.png")
    print(" -> C:/thesis/chua_manifold_sync.png")
    print(" -> C:/thesis/chua_error_convergence.png")
    plt.show()

if __name__ == "__main__":
    main()
