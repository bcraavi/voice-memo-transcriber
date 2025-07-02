#!/usr/bin/env python3
"""
Helper script to process Voice Memos from your Mac
Since macOS protects Voice Memos with privacy settings, this script guides you 
through manually exporting them.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_voice_memos_access():
    """Check if we can access Voice Memos directories."""
    possible_paths = [
        Path.home() / "Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings",
        Path.home() / "Library/Application Support/com.apple.voicememos/Recordings",
        Path.home() / "Library/Containers/com.apple.VoiceMemos/Data/AvRecorder",
    ]
    
    accessible_paths = []
    for path in possible_paths:
        try:
            if path.exists() and os.access(path, os.R_OK):
                files = list(path.glob("*.m4a"))
                if files:
                    accessible_paths.append((path, files))
        except (PermissionError, OSError):
            continue
    
    return accessible_paths

def export_voice_memos_guide():
    """Provide instructions for manually exporting Voice Memos."""
    print("""
╔══════════════════════════════════════════════════════════╗
║              📱 VOICE MEMOS EXPORT GUIDE                ║
╚══════════════════════════════════════════════════════════╝

🔒 macOS protects Voice Memos with privacy settings. Here's how to export them:

📋 METHOD 1: Export from Voice Memos App
────────────────────────────────────────
1. Open the Voice Memos app
2. Select a recording you want to transcribe
3. Click the Share button (square with arrow)
4. Choose "Save to Files" or "Export to..."
5. Save to a folder like Desktop/VoiceMemos/
6. Repeat for all recordings you want to process

📋 METHOD 2: Use the Files App
──────────────────────────────
1. Open Files app
2. Go to "On My Mac" → Voice Memos
3. Select recordings and copy them
4. Paste to Desktop/VoiceMemos/ folder

📋 METHOD 3: Create Export Folder Now
─────────────────────────────────────
""")
    
    # Create export folder
    export_dir = Path.home() / "Desktop/VoiceMemos"
    export_dir.mkdir(exist_ok=True)
    
    print(f"✅ Created folder: {export_dir}")
    print(f"📁 Export your Voice Memos to this folder, then run:")
    print(f"   python process_voice_memos_folder.py")

def process_exported_memos():
    """Process voice memos from the export folder."""
    export_dir = Path.home() / "Desktop/VoiceMemos"
    
    if not export_dir.exists():
        print(f"❌ Export folder not found: {export_dir}")
        return []
    
    # Find audio files
    audio_files = []
    for pattern in ['*.m4a', '*.mp3', '*.wav', '*.mp4']:
        audio_files.extend(export_dir.glob(pattern))
    
    return [str(f) for f in audio_files]

def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║              🎙️ VOICE MEMOS PROCESSOR                    ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    # Check if we can access Voice Memos directly
    accessible = check_voice_memos_access()
    
    if accessible:
        print("🎉 Found direct access to Voice Memos!")
        for path, files in accessible:
            print(f"📁 {path}")
            print(f"   Found {len(files)} recordings")
        
        if input("\nProcess these files? (y/n): ").lower() == 'y':
            all_files = []
            for path, files in accessible:
                all_files.extend(str(f) for f in files)
            
            print(f"\n🚀 Processing {len(all_files)} Voice Memos...")
            for file_path in all_files:
                print(f"Processing: {Path(file_path).name}")
                try:
                    subprocess.run([sys.executable, "main.py", "--audio_file", file_path], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Error processing {file_path}: {e}")
    else:
        print("🔒 Cannot access Voice Memos directly due to privacy settings.")
        
        # Check export folder
        exported_files = process_exported_memos()
        
        if exported_files:
            print(f"\n✅ Found {len(exported_files)} exported files!")
            for f in exported_files:
                print(f"  📄 {Path(f).name}")
            
            if input("\nProcess these exported files? (y/n): ").lower() == 'y':
                print(f"\n🚀 Processing {len(exported_files)} files...")
                for file_path in exported_files:
                    print(f"Processing: {Path(file_path).name}")
                    try:
                        subprocess.run([sys.executable, "main.py", "--audio_file", file_path], check=True)
                    except subprocess.CalledProcessError as e:
                        print(f"Error processing {file_path}: {e}")
        else:
            export_voice_memos_guide()

if __name__ == "__main__":
    main()