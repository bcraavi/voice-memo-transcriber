#!/usr/bin/env python3
"""
Batch Transcription Script
Processes all audio files in a directory at once
"""

import os
import sys
import glob
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
import time

def find_audio_files(directory, extensions=['.wav', '.mp3', '.flac', '.ogg', '.m4a', '.mp4']):
    """Find all audio files in the specified directory"""
    audio_files = []
    for ext in extensions:
        pattern = os.path.join(directory, f"*{ext}")
        audio_files.extend(glob.glob(pattern, recursive=False))
        # Also search subdirectories
        pattern = os.path.join(directory, f"**/*{ext}")
        audio_files.extend(glob.glob(pattern, recursive=True))
    
    # Remove duplicates and sort
    audio_files = sorted(list(set(audio_files)))
    return audio_files

def process_file(audio_file, options):
    """Process a single audio file"""
    cmd = ['python', 'transcribe.py', '--audio_file', audio_file]
    
    # Add optional arguments
    if options.get('language'):
        cmd.extend(['--language', options['language']])
    if options.get('rename'):
        cmd.append('--rename')
    if options.get('segment'):
        cmd.append('--segment')
        if options.get('segment_length'):
            cmd.extend(['--segment_length', str(options['segment_length'])])
    if options.get('preprocess'):
        cmd.append('--preprocess')
    
    print(f"\n{'='*60}")
    print(f"Processing: {audio_file}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=False)
    elapsed = time.time() - start_time
    
    if result.returncode == 0:
        print(f"✅ Successfully processed in {elapsed:.1f}s")
        return True
    else:
        print(f"❌ Failed to process (error code: {result.returncode})")
        return False

def main():
    parser = argparse.ArgumentParser(description='Batch process audio files for transcription')
    parser.add_argument('directory', nargs='?', default='voice_memos', 
                        help='Directory containing audio files (default: voice_memos)')
    parser.add_argument('--language', help='Specify language code (e.g., te, en, hi)')
    parser.add_argument('--rename', action='store_true', help='Rename files based on content')
    parser.add_argument('--segment', action='store_true', help='Process long files in segments')
    parser.add_argument('--segment_length', type=int, default=5, help='Segment length in minutes')
    parser.add_argument('--preprocess', action='store_true', help='Apply noise reduction')
    parser.add_argument('--skip-processed', action='store_true', 
                        help='Skip files that have already been processed')
    
    args = parser.parse_args()
    
    # Check if directory exists
    if not os.path.exists(args.directory):
        print(f"❌ Directory '{args.directory}' does not exist!")
        sys.exit(1)
    
    # Find all audio files
    audio_files = find_audio_files(args.directory)
    
    if not audio_files:
        print(f"❌ No audio files found in '{args.directory}'")
        sys.exit(1)
    
    print(f"\n🎯 Found {len(audio_files)} audio files to process")
    print("\nFiles to process:")
    for i, file in enumerate(audio_files, 1):
        print(f"  {i}. {file}")
    
    # Confirm before processing
    response = input("\nProceed with batch transcription? (y/n): ")
    if response.lower() != 'y':
        print("Batch processing cancelled.")
        sys.exit(0)
    
    # Process options
    options = {
        'language': args.language,
        'rename': args.rename,
        'segment': args.segment,
        'segment_length': args.segment_length,
        'preprocess': args.preprocess
    }
    
    # Process each file
    successful = 0
    failed = 0
    start_time = time.time()
    
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n📊 Progress: {i}/{len(audio_files)} files")
        
        if args.skip_processed:
            # TODO: Check if already processed by querying the database
            # For now, we'll process all files
            # Future enhancement: check transcripts_metadata.db
            pass
        
        if process_file(audio_file, options):
            successful += 1
        else:
            failed += 1
    
    # Summary
    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print("📊 BATCH PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Successful: {successful} files")
    print(f"❌ Failed: {failed} files")
    print(f"⏱️  Total time: {total_time/60:.1f} minutes")
    print(f"{'='*60}")
    
    # Suggest next steps
    if successful > 0:
        print("\n💡 You can now use the Q&A interface:")
        print("   python qa.py")
        print("   python qa_multilingual.py")

if __name__ == "__main__":
    main()