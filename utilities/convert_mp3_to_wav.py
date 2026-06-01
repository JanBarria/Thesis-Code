"""
Convert MP3 to WAV (Mono, 16-bit PCM)
Converts MP3 files to the correct format for the encryption system.

NOTE: This requires pydub and ffmpeg to be installed.
"""

import os
import sys

def check_dependencies():
    """Check if required libraries are installed"""
    try:
        from pydub import AudioSegment
        return True
    except ImportError:
        return False

def convert_mp3_to_wav(input_file, output_file=None):
    """
    Convert MP3 to mono WAV file
    
    Args:
        input_file: Path to input MP3 file
        output_file: Path to output WAV file (optional)
    """
    print("=" * 60)
    print("CONVERTING MP3 TO WAV")
    print("=" * 60)
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"✗ Error: File not found: {input_file}")
        return False
    
    try:
        from pydub import AudioSegment
        
        # Load MP3 file
        print(f"Loading: {input_file}")
        audio = AudioSegment.from_mp3(input_file)
        
        print(f"✓ MP3 loaded")
        print(f"  Channels: {audio.channels}")
        print(f"  Sample rate: {audio.frame_rate} Hz")
        print(f"  Duration: {len(audio)/1000:.2f} seconds")
        
        # Convert to mono
        if audio.channels > 1:
            audio = audio.set_channels(1)
            print(f"✓ Converted to mono")
        
        # Set to 16-bit
        audio = audio.set_sample_width(2)  # 2 bytes = 16 bits
        print(f"✓ Set to 16-bit PCM")
        
        # Determine output filename
        if output_file is None:
            base = os.path.splitext(input_file)[0]
            output_file = f"{base}.wav"
        
        # Export as WAV
        audio.export(output_file, format="wav")
        
        print(f"✓ Saved WAV file to: {output_file}")
        print(f"  Format: 16-bit PCM mono WAV")
        print(f"  Sample rate: {audio.frame_rate} Hz")
        
        print("=" * 60)
        print("SUCCESS! MP3 converted to WAV.")
        print("=" * 60)
        return True
        
    except ImportError:
        print("\n✗ Error: Required libraries not installed!")
        print("\nTo convert MP3 files, you need to install:")
        print("  1. pydub library")
        print("  2. ffmpeg")
        print("\nInstallation instructions:")
        print("\n--- Step 1: Install pydub ---")
        print("pip install pydub")
        print("\n--- Step 2: Install ffmpeg ---")
        print("Windows:")
        print("  1. Download from: https://ffmpeg.org/download.html")
        print("  2. Extract to C:\\ffmpeg")
        print("  3. Add C:\\ffmpeg\\bin to PATH")
        print("\nOR use online converter:")
        print("  1. Go to: https://cloudconvert.com/mp3-to-wav")
        print("  2. Upload your MP3")
        print("  3. Download the WAV file")
        print("  4. Make sure it's mono (use convert_to_mono.py)")
        print("=" * 60)
        return False
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MP3 TO WAV CONVERTER")
    print("=" * 60)
    
    # Check dependencies first
    if not check_dependencies():
        print("\n⚠️  WARNING: pydub library not found!")
        print("\nYou have two options:")
        print("\n--- Option 1: Install pydub (Recommended) ---")
        print("Run this command:")
        print("  pip install pydub")
        print("\nThen install ffmpeg:")
        print("  Windows: Download from https://ffmpeg.org/download.html")
        print("  Mac: brew install ffmpeg")
        print("  Linux: sudo apt-get install ffmpeg")
        print("\n--- Option 2: Use Online Converter (Easier) ---")
        print("1. Go to: https://cloudconvert.com/mp3-to-wav")
        print("2. Upload your MP3 file")
        print("3. Download the converted WAV file")
        print("4. Use convert_to_mono.py to ensure it's mono")
        print("\n" + "=" * 60)
        sys.exit(1)
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python convert_mp3_to_wav.py <input.mp3>")
        print("  python convert_mp3_to_wav.py <input.mp3> <output.wav>")
        print("\nExamples:")
        print("  python convert_mp3_to_wav.py my_song.mp3")
        print("  python convert_mp3_to_wav.py song.mp3 song_converted.wav")
        print("=" * 60)
        
        # Interactive mode
        input_file = input("\nEnter path to MP3 file: ").strip()
        if not input_file:
            print("No file specified. Exiting.")
            sys.exit(1)
        
        output_file = input("Enter output WAV filename (press Enter for auto): ").strip()
        if not output_file:
            output_file = None
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Convert the file
    success = convert_mp3_to_wav(input_file, output_file)
    
    if success:
        print("\n✓ You can now use this WAV file with the encryptor!")
        sys.exit(0)
    else:
        print("\n✗ Conversion failed.")
        sys.exit(1)

# Made with Bob
