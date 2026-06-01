"""
Convert Stereo WAV to Mono WAV
Simple script to convert any stereo audio file to mono format for the encryption system.
"""

import numpy as np
from scipy.io import wavfile
import sys
import os

def convert_to_mono(input_file, output_file=None):
    """
    Convert stereo WAV file to mono
    
    Args:
        input_file: Path to input WAV file
        output_file: Path to output WAV file (optional)
    """
    print("=" * 60)
    print("CONVERTING AUDIO TO MONO")
    print("=" * 60)
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"✗ Error: File not found: {input_file}")
        return False
    
    try:
        # Load audio file
        print(f"Loading: {input_file}")
        sample_rate, audio = wavfile.read(input_file)
        
        # Check if already mono
        if audio.ndim == 1:
            print("✓ Audio is already mono!")
            print(f"  Sample rate: {sample_rate} Hz")
            print(f"  Samples: {len(audio)}")
            
            # If output file specified, copy it
            if output_file and output_file != input_file:
                wavfile.write(output_file, sample_rate, audio)
                print(f"✓ Copied to: {output_file}")
            return True
        
        # Convert stereo to mono
        print(f"✓ Audio loaded")
        print(f"  Channels: {audio.shape[1] if audio.ndim == 2 else 1}")
        print(f"  Sample rate: {sample_rate} Hz")
        print(f"  Samples: {len(audio)}")
        
        if audio.ndim == 2:
            # Average the channels
            mono = np.mean(audio, axis=1).astype(audio.dtype)
            print(f"✓ Converted to mono (averaged {audio.shape[1]} channels)")
        else:
            mono = audio
        
        # Ensure 16-bit PCM format
        if mono.dtype != np.int16:
            print(f"Converting from {mono.dtype} to int16...")
            # Normalize to int16 range
            if np.issubdtype(mono.dtype, np.floating):
                # Float audio (usually -1.0 to 1.0)
                mono = (mono * 32767).astype(np.int16)
            else:
                # Other integer types
                max_val = np.max(np.abs(mono))
                if max_val > 0:
                    mono = (mono.astype(np.float64) / max_val * 32767).astype(np.int16)
                else:
                    mono = mono.astype(np.int16)
            print("✓ Converted to 16-bit PCM")
        
        # Determine output filename
        if output_file is None:
            # Create output filename by adding _mono before extension
            base, ext = os.path.splitext(input_file)
            output_file = f"{base}_mono{ext}"
        
        # Save mono audio
        wavfile.write(output_file, sample_rate, mono)
        print(f"✓ Saved mono audio to: {output_file}")
        print(f"  Sample rate: {sample_rate} Hz")
        print(f"  Samples: {len(mono)}")
        print(f"  Format: 16-bit PCM mono")
        
        print("=" * 60)
        print("SUCCESS! Audio converted to mono.")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("WAV TO MONO CONVERTER")
    print("=" * 60)
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python convert_to_mono.py <input.wav>")
        print("  python convert_to_mono.py <input.wav> <output.wav>")
        print("\nExamples:")
        print("  python convert_to_mono.py my_audio.wav")
        print("  python convert_to_mono.py stereo.wav mono.wav")
        print("\nIf output filename is not specified,")
        print("it will create: input_mono.wav")
        print("=" * 60)
        
        # Interactive mode
        input_file = input("\nEnter path to WAV file to convert: ").strip()
        if not input_file:
            print("No file specified. Exiting.")
            sys.exit(1)
        
        output_file = input("Enter output filename (press Enter for auto): ").strip()
        if not output_file:
            output_file = None
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Convert the file
    success = convert_to_mono(input_file, output_file)
    
    if success:
        print("\n✓ You can now use this file with the encryptor!")
        sys.exit(0)
    else:
        print("\n✗ Conversion failed.")
        sys.exit(1)

# Made with Bob
