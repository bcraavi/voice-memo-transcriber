#!/usr/bin/env python3
"""
Show all processed transcripts and their contents
"""

import chromadb
from chromadb.config import Settings
import json

def show_all_transcripts():
    """Display all transcripts in the database."""
    print("📚 All Your Processed Audio Transcripts")
    print("=" * 50)
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get the collection
        collection = client.get_collection("audio_transcripts")
        
        # Get all documents
        results = collection.get()
        
        if not results['documents']:
            print("No transcripts found.")
            return
        
        # Group by audio file
        audio_files = {}
        for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
            file_name = metadata.get('audio_file', 'Unknown')
            if file_name not in audio_files:
                audio_files[file_name] = []
            
            audio_files[file_name].append({
                'text': doc,
                'speaker': metadata.get('speaker', 'Unknown'),
                'start': metadata.get('start_time', 0),
                'end': metadata.get('end_time', 0)
            })
        
        # Display results
        print(f"Found transcripts from {len(audio_files)} audio file(s):\n")
        
        for file_name, segments in audio_files.items():
            print(f"🎵 {file_name}")
            print("-" * len(file_name))
            
            # Sort segments by time
            segments.sort(key=lambda x: x['start'])
            
            for segment in segments:
                time_str = f"{segment['start']:.1f}s-{segment['end']:.1f}s"
                print(f"[{time_str}] {segment['text']}")
            
            print()
        
        print(f"📊 Summary:")
        print(f"• Total audio files: {len(audio_files)}")
        print(f"• Total segments: {len(results['documents'])}")
        
        # Calculate total duration
        total_duration = 0
        for segments in audio_files.values():
            if segments:
                total_duration += max(seg['end'] for seg in segments)
        
        print(f"• Approximate total duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    show_all_transcripts()