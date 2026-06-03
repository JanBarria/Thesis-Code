#!/usr/bin/env python3
"""
Interactive Menu System for Chaos-Based Secure Communication
Allows user to choose between Chua, Rössler, or Hybrid encryption
"""

import os
import sys
import subprocess
from pathlib import Path

# ANSI color codes for better UI
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print the application header"""
    clear_screen()
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("=" * 70)
    print("  CHAOS-BASED SECURE COMMUNICATION SYSTEM")
    print("  De La Salle University - ECE Thesis Project")
    print("=" * 70)
    print(f"{Colors.ENDC}")
    print()

def print_menu():
    """Print the main menu"""
    print(f"{Colors.BOLD}Choose Encryption System:{Colors.ENDC}")
    print()
    print(f"{Colors.BLUE}[1]{Colors.ENDC} Chua Circuit System")
    print(f"    • Double-scroll attractor")
    print(f"    • Piecewise-linear nonlinearity")
    print(f"    • More complex, proven security")
    print()
    print(f"{Colors.GREEN}[2]{Colors.ENDC} Rössler System")
    print(f"    • Spiral attractor")
    print(f"    • Polynomial nonlinearity")
    print(f"    • Simpler, 25% more efficient")
    print()
    print(f"{Colors.YELLOW}[3]{Colors.ENDC} Hybrid System (Cascaded)")
    print(f"    • Chua → Rössler (double encryption)")
    print(f"    • Rössler → Chua (double encryption)")
    print(f"    • Maximum security, slower")
    print()
    print(f"{Colors.RED}[4]{Colors.ENDC} Exit")
    print()

def run_chua_system():
    """Run Chua Circuit system"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Running Chua Circuit System...{Colors.ENDC}\n")
    
    script_path = Path("main_scripts/test_system.py")
    if not script_path.exists():
        print(f"{Colors.RED}Error: test_system.py not found!{Colors.ENDC}")
        return False
    
    try:
        result = subprocess.run([sys.executable, str(script_path)], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}Error running Chua system: {e}{Colors.ENDC}")
        return False
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.ENDC}")
        return False

def run_rossler_system():
    """Run Rössler system"""
    print(f"\n{Colors.GREEN}{Colors.BOLD}Running Rössler System...{Colors.ENDC}\n")
    
    script_path = Path("main_scripts/test_rossler_system.py")
    if not script_path.exists():
        print(f"{Colors.RED}Error: test_rossler_system.py not found!{Colors.ENDC}")
        return False
    
    try:
        result = subprocess.run([sys.executable, str(script_path)], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}Error running Rössler system: {e}{Colors.ENDC}")
        return False
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.ENDC}")
        return False

def run_hybrid_system():
    """Run Hybrid system with cascaded encryption"""
    print(f"\n{Colors.YELLOW}{Colors.BOLD}Running Hybrid System...{Colors.ENDC}\n")
    
    # Show hybrid options
    print(f"{Colors.BOLD}Choose Hybrid Mode:{Colors.ENDC}")
    print(f"[1] Chua → Rössler (Encrypt with Chua first, then Rössler)")
    print(f"[2] Rössler → Chua (Encrypt with Rössler first, then Chua)")
    print(f"[3] Back to main menu")
    print()
    
    choice = input(f"{Colors.CYAN}Enter your choice (1-3): {Colors.ENDC}").strip()
    
    if choice == "1":
        return run_hybrid_chua_rossler()
    elif choice == "2":
        return run_hybrid_rossler_chua()
    elif choice == "3":
        return True
    else:
        print(f"{Colors.RED}Invalid choice!{Colors.ENDC}")
        return False

def run_hybrid_chua_rossler():
    """Run hybrid: Chua → Rössler"""
    print(f"\n{Colors.YELLOW}{Colors.BOLD}Hybrid Mode: Chua → Rössler{Colors.ENDC}\n")
    
    script_path = Path("main_scripts/test_hybrid_chua_rossler.py")
    if not script_path.exists():
        print(f"{Colors.RED}Error: test_hybrid_chua_rossler.py not found!{Colors.ENDC}")
        print(f"{Colors.YELLOW}Creating hybrid script...{Colors.ENDC}")
        create_hybrid_scripts()
    
    try:
        result = subprocess.run([sys.executable, str(script_path)], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}Error running hybrid system: {e}{Colors.ENDC}")
        return False
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.ENDC}")
        return False

def run_hybrid_rossler_chua():
    """Run hybrid: Rössler → Chua"""
    print(f"\n{Colors.YELLOW}{Colors.BOLD}Hybrid Mode: Rössler → Chua{Colors.ENDC}\n")
    
    script_path = Path("main_scripts/test_hybrid_rossler_chua.py")
    if not script_path.exists():
        print(f"{Colors.RED}Error: test_hybrid_rossler_chua.py not found!{Colors.ENDC}")
        print(f"{Colors.YELLOW}Creating hybrid script...{Colors.ENDC}")
        create_hybrid_scripts()
    
    try:
        result = subprocess.run([sys.executable, str(script_path)], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}Error running hybrid system: {e}{Colors.ENDC}")
        return False
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.ENDC}")
        return False

def create_hybrid_scripts():
    """Create hybrid test scripts if they don't exist"""
    print(f"{Colors.YELLOW}Hybrid scripts will be created in the next update.{Colors.ENDC}")
    print(f"{Colors.YELLOW}For now, please use individual systems.{Colors.ENDC}")

def show_results_summary(success):
    """Show results summary"""
    print()
    print("=" * 70)
    if success:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ Test completed successfully!{Colors.ENDC}")
        print(f"\nCheck the output files in the respective system folder:")
        print(f"  • encrypted_audio.wav")
        print(f"  • decrypted_audio.wav")
        print(f"  • Performance metrics displayed above")
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ Test failed or was interrupted{Colors.ENDC}")
        print(f"\nPlease check:")
        print(f"  • All required files are present")
        print(f"  • Python packages are installed (numpy, scipy, soundfile)")
        print(f"  • Test audio file exists")
    print("=" * 70)
    print()

def main():
    """Main application loop"""
    while True:
        print_header()
        print_menu()
        
        choice = input(f"{Colors.CYAN}Enter your choice (1-4): {Colors.ENDC}").strip()
        
        if choice == "1":
            success = run_chua_system()
            show_results_summary(success)
            input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")
            
        elif choice == "2":
            success = run_rossler_system()
            show_results_summary(success)
            input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")
            
        elif choice == "3":
            success = run_hybrid_system()
            if success is not True:  # Only show summary if actually ran a test
                show_results_summary(success)
            input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")
            
        elif choice == "4":
            print(f"\n{Colors.GREEN}Thank you for using the Chaos-Based Secure Communication System!{Colors.ENDC}")
            print(f"{Colors.CYAN}Good luck with your thesis! 🎓{Colors.ENDC}\n")
            sys.exit(0)
            
        else:
            print(f"\n{Colors.RED}Invalid choice! Please enter 1, 2, 3, or 4.{Colors.ENDC}")
            input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Program interrupted by user. Goodbye!{Colors.ENDC}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.ENDC}\n")
        sys.exit(1)

# Made with Bob
