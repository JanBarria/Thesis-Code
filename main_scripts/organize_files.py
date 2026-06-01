"""
Organize files into proper folders
"""
import os
import shutil

print("=" * 80)
print("ORGANIZING FILES INTO FOLDERS")
print("=" * 80)

# Create organized folder structure
folders = {
    'documentation': [
        'README.md',
        'TESTING_ON_PC.md',
        'HOW_TO_RUN.md',
        'RUN_IN_PYTHON.md',
        'PERFECT_RESULTS_GUIDE.md',
        'RUN_TEST_SYSTEM.md',
        'SIMPLE_STEPS.md',
        'FINAL_STEP_BY_STEP_GUIDE.md',
        'COMPARISON_TABLE.md',
        'SOLUTION.md'
    ],
    'utilities': [
        'create_test_audio.py',
        'convert_to_mono.py',
        'convert_mp3_to_wav.py',
        'clean_and_test.py',
        'diagnose_problem.py',
        'debug_sync.py',
        'test_perfect_results.py'
    ],
    'main_scripts': [
        'test_system.py',
        'organize_files.py'
    ]
}

# Create folders
for folder in folders.keys():
    os.makedirs(folder, exist_ok=True)
    print(f"\n✓ Created folder: {folder}/")

# Move files
print("\nMoving files...")
for folder, files in folders.items():
    for file in files:
        if os.path.exists(file):
            try:
                shutil.move(file, f"{folder}/{file}")
                print(f"  ✓ Moved {file} → {folder}/")
            except Exception as e:
                print(f"  ✗ Could not move {file}: {e}")

print("\n" + "=" * 80)
print("FILE ORGANIZATION COMPLETE!")
print("=" * 80)

print("\nNew folder structure:")
print("chaos_secure_communication/")
print("  ├── chua_system/          (Chua circuit modules)")
print("  ├── rossler_system/       (Rössler system modules)")
print("  ├── documentation/        (All guides and README files)")
print("  ├── utilities/            (Helper scripts)")
print("  ├── main_scripts/         (Main test scripts)")
print("  └── test_audio/           (Test audio files)")

print("\n" + "=" * 80)
print("To run the system test:")
print("  python main_scripts/test_system.py")
print("=" * 80)

# Made with Bob
