#!/usr/bin/env python3
"""
analyze_sync.py - Synchronization Analysis Script

Analyzes data from master_data.csv and slave_data.csv to verify
Pecora-Carroll synchronization quality.

Generates:
1. Time-series plots comparing master and slave states
2. Synchronization error plots: e(t) = |x_slave(t) - x_master(t)|
3. Pearson correlation coefficients for x, y, z
4. Phase space plots (x vs y, x vs z)

Target: Correlation coefficient r >= 0.95 (from thesis Section 4.7)
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import sys

# Configuration
MASTER_FILE = "master_data.csv"
SLAVE_FILE = "slave_data.csv"
OUTPUT_DIR = "analysis_results"

def load_data(filename):
    """Load CSV data file"""
    try:
        data = np.loadtxt(filename, delimiter=',', skiprows=1)
        return data
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None

def align_data(master_data, slave_data):
    """Align master and slave data by interpolating to common time base"""
    # Extract time and states
    t_master = master_data[:, 0]
    x_master = master_data[:, 1]
    y_master = master_data[:, 2]
    z_master = master_data[:, 3]
    
    t_slave = slave_data[:, 0]
    x_drive = slave_data[:, 1]  # x received from master
    x_slave = slave_data[:, 2]
    y_slave = slave_data[:, 3]
    z_slave = slave_data[:, 4]
    
    # Find common time range
    t_start = max(t_master[0], t_slave[0])
    t_end = min(t_master[-1], t_slave[-1])
    
    # Create common time base (use master's sampling)
    mask_master = (t_master >= t_start) & (t_master <= t_end)
    t_common = t_master[mask_master]
    
    # Interpolate slave data to master's time base
    x_drive_interp = np.interp(t_common, t_slave, x_drive)
    x_slave_interp = np.interp(t_common, t_slave, x_slave)
    y_slave_interp = np.interp(t_common, t_slave, y_slave)
    z_slave_interp = np.interp(t_common, t_slave, z_slave)
    
    # Get corresponding master data
    x_master_aligned = x_master[mask_master]
    y_master_aligned = y_master[mask_master]
    z_master_aligned = z_master[mask_master]
    
    return {
        't': t_common,
        'x_master': x_master_aligned,
        'y_master': y_master_aligned,
        'z_master': z_master_aligned,
        'x_drive': x_drive_interp,
        'x_slave': x_slave_interp,
        'y_slave': y_slave_interp,
        'z_slave': z_slave_interp
    }

def calculate_sync_error(data):
    """Calculate synchronization errors"""
    e_x = np.abs(data['x_slave'] - data['x_master'])
    e_y = np.abs(data['y_slave'] - data['y_master'])
    e_z = np.abs(data['z_slave'] - data['z_master'])
    
    return e_x, e_y, e_z

def calculate_correlations(data):
    """Calculate Pearson correlation coefficients"""
    r_x, p_x = stats.pearsonr(data['x_master'], data['x_slave'])
    r_y, p_y = stats.pearsonr(data['y_master'], data['y_slave'])
    r_z, p_z = stats.pearsonr(data['z_master'], data['z_slave'])
    
    return {
        'r_x': r_x, 'p_x': p_x,
        'r_y': r_y, 'p_y': p_y,
        'r_z': r_z, 'p_z': p_z
    }

def plot_time_series(data, e_x, e_y, e_z):
    """Generate time-series comparison plots"""
    fig, axes = plt.subplots(4, 1, figsize=(12, 10))
    fig.suptitle('Chaos Synchronization: Time Series Comparison', fontsize=14, fontweight='bold')
    
    t = data['t']
    
    # X state
    axes[0].plot(t, data['x_master'], 'b-', label='Master x', linewidth=1.5, alpha=0.7)
    axes[0].plot(t, data['x_slave'], 'r--', label='Slave x', linewidth=1.5, alpha=0.7)
    axes[0].set_ylabel('x(t)')
    axes[0].legend(loc='upper right')
    axes[0].grid(True, alpha=0.3)
    
    # Y state
    axes[1].plot(t, data['y_master'], 'b-', label='Master y', linewidth=1.5, alpha=0.7)
    axes[1].plot(t, data['y_slave'], 'r--', label='Slave y', linewidth=1.5, alpha=0.7)
    axes[1].set_ylabel('y(t)')
    axes[1].legend(loc='upper right')
    axes[1].grid(True, alpha=0.3)
    
    # Z state
    axes[2].plot(t, data['z_master'], 'b-', label='Master z', linewidth=1.5, alpha=0.7)
    axes[2].plot(t, data['z_slave'], 'r--', label='Slave z', linewidth=1.5, alpha=0.7)
    axes[2].set_ylabel('z(t)')
    axes[2].legend(loc='upper right')
    axes[2].grid(True, alpha=0.3)
    
    # Synchronization error
    axes[3].semilogy(t, e_x, 'g-', label='|x_slave - x_master|', linewidth=1.5, alpha=0.7)
    axes[3].semilogy(t, e_y, 'm-', label='|y_slave - y_master|', linewidth=1.5, alpha=0.7)
    axes[3].semilogy(t, e_z, 'c-', label='|z_slave - z_master|', linewidth=1.5, alpha=0.7)
    axes[3].set_xlabel('Time (s)')
    axes[3].set_ylabel('Sync Error (log scale)')
    axes[3].legend(loc='upper right')
    axes[3].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/time_series.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {OUTPUT_DIR}/time_series.png")
    plt.close()

def plot_phase_space(data):
    """Generate phase space plots"""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Chaos Synchronization: Phase Space', fontsize=14, fontweight='bold')
    
    # Master x-y
    axes[0, 0].plot(data['x_master'], data['y_master'], 'b-', linewidth=0.5, alpha=0.6)
    axes[0, 0].set_xlabel('x')
    axes[0, 0].set_ylabel('y')
    axes[0, 0].set_title('Master: x vs y')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Slave x-y
    axes[0, 1].plot(data['x_slave'], data['y_slave'], 'r-', linewidth=0.5, alpha=0.6)
    axes[0, 1].set_xlabel('x')
    axes[0, 1].set_ylabel('y')
    axes[0, 1].set_title('Slave: x vs y')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Master x-z
    axes[1, 0].plot(data['x_master'], data['z_master'], 'b-', linewidth=0.5, alpha=0.6)
    axes[1, 0].set_xlabel('x')
    axes[1, 0].set_ylabel('z')
    axes[1, 0].set_title('Master: x vs z')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Slave x-z
    axes[1, 1].plot(data['x_slave'], data['z_slave'], 'r-', linewidth=0.5, alpha=0.6)
    axes[1, 1].set_xlabel('x')
    axes[1, 1].set_ylabel('z')
    axes[1, 1].set_title('Slave: x vs z')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/phase_space.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {OUTPUT_DIR}/phase_space.png")
    plt.close()

def plot_correlation(data):
    """Generate correlation scatter plots"""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle('Chaos Synchronization: Correlation Analysis', fontsize=14, fontweight='bold')
    
    # X correlation
    axes[0].scatter(data['x_master'], data['x_slave'], s=1, alpha=0.5)
    axes[0].plot([data['x_master'].min(), data['x_master'].max()],
                 [data['x_master'].min(), data['x_master'].max()],
                 'r--', linewidth=2, label='Perfect sync')
    axes[0].set_xlabel('Master x')
    axes[0].set_ylabel('Slave x')
    axes[0].set_title('x State Correlation')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Y correlation
    axes[1].scatter(data['y_master'], data['y_slave'], s=1, alpha=0.5)
    axes[1].plot([data['y_master'].min(), data['y_master'].max()],
                 [data['y_master'].min(), data['y_master'].max()],
                 'r--', linewidth=2, label='Perfect sync')
    axes[1].set_xlabel('Master y')
    axes[1].set_ylabel('Slave y')
    axes[1].set_title('y State Correlation')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    # Z correlation
    axes[2].scatter(data['z_master'], data['z_slave'], s=1, alpha=0.5)
    axes[2].plot([data['z_master'].min(), data['z_master'].max()],
                 [data['z_master'].min(), data['z_master'].max()],
                 'r--', linewidth=2, label='Perfect sync')
    axes[2].set_xlabel('Master z')
    axes[2].set_ylabel('Slave z')
    axes[2].set_title('z State Correlation')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/correlation.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {OUTPUT_DIR}/correlation.png")
    plt.close()

def generate_report(data, e_x, e_y, e_z, corr):
    """Generate text report"""
    report = []
    report.append("="*70)
    report.append("CHAOS SYNCHRONIZATION ANALYSIS REPORT")
    report.append("="*70)
    report.append("")
    
    # Data statistics
    report.append("DATA STATISTICS:")
    report.append(f"  Number of samples: {len(data['t'])}")
    report.append(f"  Time range: {data['t'][0]:.3f} - {data['t'][-1]:.3f} seconds")
    report.append(f"  Duration: {data['t'][-1] - data['t'][0]:.3f} seconds")
    report.append("")
    
    # Synchronization error statistics
    report.append("SYNCHRONIZATION ERROR STATISTICS:")
    report.append(f"  X error - Mean: {np.mean(e_x):.6f}, Std: {np.std(e_x):.6f}, Max: {np.max(e_x):.6f}")
    report.append(f"  Y error - Mean: {np.mean(e_y):.6f}, Std: {np.std(e_y):.6f}, Max: {np.max(e_y):.6f}")
    report.append(f"  Z error - Mean: {np.mean(e_z):.6f}, Std: {np.std(e_z):.6f}, Max: {np.max(e_z):.6f}")
    report.append("")
    
    # Correlation coefficients
    report.append("PEARSON CORRELATION COEFFICIENTS:")
    report.append(f"  X: r = {corr['r_x']:.6f} (p = {corr['p_x']:.2e})")
    report.append(f"  Y: r = {corr['r_y']:.6f} (p = {corr['p_y']:.2e})")
    report.append(f"  Z: r = {corr['r_z']:.6f} (p = {corr['p_z']:.2e})")
    report.append("")
    
    # Thesis target evaluation
    report.append("THESIS TARGET EVALUATION (r >= 0.95):")
    target = 0.95
    report.append(f"  X: {'PASS' if corr['r_x'] >= target else 'FAIL'} ({corr['r_x']:.6f})")
    report.append(f"  Y: {'PASS' if corr['r_y'] >= target else 'FAIL'} ({corr['r_y']:.6f})")
    report.append(f"  Z: {'PASS' if corr['r_z'] >= target else 'FAIL'} ({corr['r_z']:.6f})")
    report.append("")
    
    # Overall assessment
    all_pass = all([corr['r_x'] >= target, corr['r_y'] >= target, corr['r_z'] >= target])
    report.append("OVERALL ASSESSMENT:")
    if all_pass:
        report.append("  ✓ SYNCHRONIZATION SUCCESSFUL - All states meet target threshold")
    else:
        report.append("  ✗ SYNCHRONIZATION INCOMPLETE - Some states below target threshold")
    report.append("")
    report.append("="*70)
    
    # Print to console
    report_text = "\n".join(report)
    print(report_text)
    
    # Save to file
    with open(f'{OUTPUT_DIR}/report.txt', 'w') as f:
        f.write(report_text)
    print(f"\nSaved: {OUTPUT_DIR}/report.txt")

def main():
    """Main analysis function"""
    import os
    
    print("="*70)
    print("CHAOS SYNCHRONIZATION ANALYSIS")
    print("="*70)
    print()
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load data
    print("Loading data files...")
    master_data = load_data(MASTER_FILE)
    slave_data = load_data(SLAVE_FILE)
    
    if master_data is None or slave_data is None:
        print("Error: Could not load data files")
        sys.exit(1)
    
    print(f"  Master: {len(master_data)} samples")
    print(f"  Slave: {len(slave_data)} samples")
    print()
    
    # Align data
    print("Aligning data to common time base...")
    data = align_data(master_data, slave_data)
    print(f"  Aligned: {len(data['t'])} samples")
    print()
    
    # Calculate synchronization error
    print("Calculating synchronization error...")
    e_x, e_y, e_z = calculate_sync_error(data)
    print()
    
    # Calculate correlations
    print("Calculating correlation coefficients...")
    corr = calculate_correlations(data)
    print()
    
    # Generate plots
    print("Generating plots...")
    plot_time_series(data, e_x, e_y, e_z)
    plot_phase_space(data)
    plot_correlation(data)
    print()
    
    # Generate report
    print("Generating report...")
    generate_report(data, e_x, e_y, e_z, corr)
    print()
    
    print("Analysis complete!")

if __name__ == "__main__":
    main()

# Made with Bob
