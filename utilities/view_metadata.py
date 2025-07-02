#!/usr/bin/env python3
"""
View metadata for processed audio files.
Shows original filenames, new titles, languages, and processing dates.
"""

import sqlite3
import argparse
from pathlib import Path
from datetime import datetime


def show_metadata(db_path="transcripts_metadata.db"):
    """Display all stored file metadata."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all metadata
        cursor.execute("""
            SELECT file_hash, original_path, new_path, title, language, 
                   duration_seconds, processed_date
            FROM file_metadata
            ORDER BY processed_date DESC
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            print("No processed files found in metadata database.")
            return
        
        print(f"\n{'='*100}")
        print(f"{'Processed Audio Files Metadata':^100}")
        print(f"{'='*100}\n")
        
        for row in rows:
            (file_hash, original_path, new_path, title, language, 
             duration_seconds, processed_date) = row
            
            print(f"Original File: {Path(original_path).name}")
            if new_path != original_path:
                print(f"Renamed To: {Path(new_path).name}")
            print(f"Title: {title}")
            print(f"Language: {language}")
            print(f"Duration: {duration_seconds/60:.1f} minutes")
            print(f"File Hash: {file_hash[:16]}...")
            
            # Format date
            try:
                date_obj = datetime.fromisoformat(processed_date)
                print(f"Processed: {date_obj.strftime('%Y-%m-%d %H:%M:%S')}")
            except:
                print(f"Processed: {processed_date}")
            
            print("-" * 100)
        
        print(f"\nTotal files processed: {len(rows)}")
        
        # Language statistics
        cursor.execute("""
            SELECT language, COUNT(*) as count
            FROM file_metadata
            GROUP BY language
            ORDER BY count DESC
        """)
        
        lang_stats = cursor.fetchall()
        if lang_stats:
            print("\nLanguage Distribution:")
            for lang, count in lang_stats:
                print(f"  {lang}: {count} file(s)")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")


def search_by_language(language, db_path="transcripts_metadata.db"):
    """Search for files by language."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT original_path, new_path, title, processed_date
            FROM file_metadata
            WHERE language = ?
            ORDER BY processed_date DESC
        """, (language,))
        
        rows = cursor.fetchall()
        
        if not rows:
            print(f"No files found for language: {language}")
            return
        
        print(f"\nFiles in {language}:")
        print("-" * 80)
        
        for original_path, new_path, title, processed_date in rows:
            print(f"Title: {title}")
            print(f"File: {Path(new_path).name}")
            print(f"Date: {processed_date}")
            print("-" * 80)
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="View audio transcription metadata")
    parser.add_argument(
        "--language",
        type=str,
        help="Filter by language code (e.g., en, es, fr)"
    )
    parser.add_argument(
        "--db",
        type=str,
        default="transcripts_metadata.db",
        help="Path to metadata database"
    )
    
    args = parser.parse_args()
    
    if args.language:
        search_by_language(args.language, args.db)
    else:
        show_metadata(args.db)


if __name__ == "__main__":
    main()