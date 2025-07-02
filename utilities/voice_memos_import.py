#!/usr/bin/env python3
"""
Import and process Voice Memos from macOS
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

def find_voice_memos():
    """Find voice memo files on the system."""
    print("🔍 Searching for Voice Memos...")
    
    # Common locations and patterns
    search_paths = [
        # iCloud Drive Voice Memos
        Path.home() / "Library/Mobile Documents/com~apple~VoiceMemos/Documents",
        Path.home() / "Library/Mobile Documents/iCloud~com~apple~VoiceMemos/Documents",
        
        # Local Voice Memos
        Path.home() / "Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings",
        Path.home() / "Library/Containers/com.apple.VoiceMemos/Data/AvRecorder",
        
        # Downloads or Desktop (if exported)
        Path.home() / "Downloads",
        Path.home() / "Desktop",
    ]
    
    found_files = []
    
    # Search using mdfind (Spotlight)
    try:
        # Search for m4a files with "Recording" or "Voice Memo" in the name
        cmd = [
            "mdfind",
            "-onlyin", str(Path.home()),
            "(kMDItemContentType == 'com.apple.m4a-audio' || kMDItemContentType == 'public.mpeg-4-audio') && (kMDItemDisplayName == '*Recording*' || kMDItemDisplayName == '*Voice*Memo*')"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout:
            for line in result.stdout.strip().split('\n'):
                if line and os.path.exists(line):
                    found_files.append(line)
    except Exception as e:
        print(f"Spotlight search error: {e}")
    
    # Manual search in common locations
    for search_path in search_paths:
        if search_path.exists():
            try:
                # Look for audio files
                for pattern in ['*.m4a', '*.mp4', '*.wav', '*.mp3']:
                    found_files.extend(str(f) for f in search_path.glob(pattern))
                    found_files.extend(str(f) for f in search_path.glob(f"**/{pattern}"))
            except PermissionError:
                print(f"⚠️  Permission denied: {search_path}")
    
    # Remove duplicates and sort
    found_files = sorted(list(set(found_files)))
    
    return found_files

def copy_voice_memos(files, destination="voice_memos"):
    """Copy voice memos to a local directory."""
    dest_path = Path(destination)
    dest_path.mkdir(exist_ok=True)
    
    copied_files = []
    
    for file_path in files:
        try:
            source = Path(file_path)
            # Create a clean filename
            timestamp = datetime.fromtimestamp(source.stat().st_mtime).strftime("%Y%m%d_%H%M%S")
            clean_name = f"{timestamp}_{source.name}"
            dest_file = dest_path / clean_name
            
            shutil.copy2(source, dest_file)
            copied_files.append(str(dest_file))
            print(f"✓ Copied: {source.name} → {clean_name}")
            
        except Exception as e:
            print(f"✗ Error copying {file_path}: {e}")
    
    return copied_files

def process_voice_memos(files):
    """Process voice memos with the transcription system."""
    print(f"\n📋 Processing {len(files)} voice memos...")
    
    for i, file_path in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] Processing: {Path(file_path).name}")
        print("-" * 50)
        
        # Run the transcription
        cmd = [sys.executable, "main.py", "--audio_file", file_path]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error processing {file_path}: {e}")
        except KeyboardInterrupt:
            print("\n\nProcessing interrupted by user.")
            break

def main():
    print("""
╔══════════════════════════════════════════╗
║      Voice Memos Import & Process        ║
╚══════════════════════════════════════════╝
""")
    
    # Find voice memos
    voice_memos = find_voice_memos()
    
    if not voice_memos:
        print("\n❌ No Voice Memos found.")
        print("\nTip: If you have Voice Memos on iCloud, make sure they're downloaded.")
        print("You can also manually export them from the Voice Memos app:")
        print("1. Open Voice Memos app")
        print("2. Select a recording")
        print("3. Click Share button → Save to Files")
        print("4. Save to Downloads or Desktop")
        return
    
    print(f"\n✅ Found {len(voice_memos)} voice memo(s):")
    for i, memo in enumerate(voice_memos[:10], 1):  # Show first 10
        print(f"{i}. {Path(memo).name}")
    
    if len(voice_memos) > 10:
        print(f"... and {len(voice_memos) - 10} more")
    
    # Ask user what to do
    print("\nOptions:")
    print("1. Copy all voice memos to local directory and process")
    print("2. Process voice memos in place")
    print("3. Just copy voice memos (no processing)")
    print("4. Cancel")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        # Copy and process
        copied = copy_voice_memos(voice_memos)
        if copied:
            process_voice_memos(copied)
    elif choice == "2":
        # Process in place
        process_voice_memos(voice_memos)
    elif choice == "3":
        # Just copy
        copy_voice_memos(voice_memos)
        print("\n✅ Voice memos copied to 'voice_memos' directory")
    else:
        print("Cancelled.")

if __name__ == "__main__":
    main()