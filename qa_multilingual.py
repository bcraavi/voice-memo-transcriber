#!/usr/bin/env python3
"""
Telugu-English Q&A Interface
Optimized for multilingual queries and responses.
"""

import argparse
import os
# Disable ChromaDB telemetry to avoid errors
os.environ["ANONYMIZED_TELEMETRY"] = "False"
from transcribe import TranscriptQA


class TeluguEnglishQA:
    def __init__(self):
        self.qa_system = TranscriptQA()
        
    def ask_multilingual_question(self, question, language_filter=None):
        """Ask questions with optional language filtering."""
        
        print(f"\n🔍 Searching for: {question}")
        if language_filter:
            print(f"   Filtering by language: {language_filter}")
        
        # For now, use the existing Q&A system
        # Future enhancement: could filter by language in ChromaDB query
        answer = self.qa_system.ask_question(question)
        
        return answer
    
    def interactive_session(self):
        """Run interactive multilingual Q&A session."""
        
        print("🌐 Telugu-English Audio Q&A System")
        print("=" * 50)
        print("Ask questions in Telugu or English about your transcripts!")
        print("Commands:")
        print("  'quit' or 'exit' - Exit the session")
        print("  'list' - Show all processed audio files")
        print("  'stats' - Show language statistics")
        print("  'telugu' - Filter to Telugu content only")
        print("  'english' - Filter to English content only")
        print("  'all' - Search all languages")
        print("-" * 50)
        
        language_filter = None
        
        while True:
            try:
                question = input(f"\n{'[All]' if not language_filter else f'[{language_filter.title()}]'} Your question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if question.lower() == 'list':
                    self.show_audio_list()
                    continue
                
                if question.lower() == 'stats':
                    self.show_language_stats()
                    continue
                
                if question.lower() == 'telugu':
                    language_filter = 'te'
                    print("🔸 Now filtering to Telugu content only")
                    continue
                
                if question.lower() == 'english':
                    language_filter = 'en'
                    print("🔸 Now filtering to English content only")
                    continue
                
                if question.lower() == 'all':
                    language_filter = None
                    print("🔸 Now searching all languages")
                    continue
                
                if not question:
                    print("Please enter a question.")
                    continue
                
                # Ask the question
                answer = self.ask_multilingual_question(question, language_filter)
                print(f"\n💬 Answer: {answer}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def show_audio_list(self):
        """Show list of all processed audio files with titles."""
        try:
            import sqlite3
            from transcribe import METADATA_DB, TranscriptQA
            
            conn = sqlite3.connect(METADATA_DB)
            cursor = conn.cursor()
            
            print("\n📚 Processed Audio Files:")
            print("=" * 60)
            
            cursor.execute("""
                SELECT original_path, new_path, title, language, 
                       duration_seconds, processed_date
                FROM file_metadata 
                ORDER BY processed_date DESC
            """)
            
            results = cursor.fetchall()
            
            if not results:
                print("   No audio files processed yet.")
                print("   Use the main script to process some audio files first!")
                conn.close()
                return
            
            for i, (original_path, new_path, title, language, duration, date) in enumerate(results, 1):
                # Extract just the filename
                import os
                original_name = os.path.basename(original_path)
                new_name = os.path.basename(new_path) if new_path != original_path else None
                
                # Language display
                lang_display = {
                    'te': 'Telugu (తెలుగు)',
                    'en': 'English',
                    'hi': 'Hindi (हिंदी)',
                    'ta': 'Tamil (தமிழ்)'
                }.get(language, language.upper())
                
                # Duration formatting
                duration_min = duration / 60 if duration else 0
                
                print(f"\n{i}. 📄 {title}")
                print(f"   🎵 Original: {original_name}")
                if new_name and new_name != original_name:
                    print(f"   📝 Renamed: {new_name}")
                print(f"   🌐 Language: {lang_display}")
                print(f"   ⏱️  Duration: {duration_min:.1f} minutes")
                
                # Format date
                try:
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(date)
                    formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
                    print(f"   📅 Processed: {formatted_date}")
                except:
                    print(f"   📅 Processed: {date}")
                
                print("   " + "-" * 50)
            
            print(f"\n📊 Total: {len(results)} audio files processed")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Could not retrieve audio list: {e}")
    
    def show_language_stats(self):
        """Show statistics about processed languages."""
        try:
            import sqlite3
            from transcribe import METADATA_DB, TranscriptQA
            
            conn = sqlite3.connect(METADATA_DB)
            cursor = conn.cursor()
            
            print("\n📊 Language Statistics:")
            print("-" * 30)
            
            # Total files by language
            cursor.execute("""
                SELECT language, COUNT(*) as count, 
                       SUM(duration_seconds)/60 as total_minutes,
                       AVG(duration_seconds)/60 as avg_minutes
                FROM file_metadata 
                GROUP BY language 
                ORDER BY count DESC
            """)
            
            results = cursor.fetchall()
            total_files = sum(row[1] for row in results)
            total_duration = sum(row[2] for row in results)
            
            for lang, count, total_min, avg_min in results:
                lang_name = {
                    'te': 'Telugu (తెలుగు)',
                    'en': 'English',
                    'hi': 'Hindi (हिंदी)',
                    'ta': 'Tamil (தமிழ்)'
                }.get(lang, lang.upper())
                
                percentage = (count / total_files) * 100 if total_files > 0 else 0
                
                print(f"  {lang_name}:")
                print(f"    Files: {count} ({percentage:.1f}%)")
                print(f"    Duration: {total_min:.1f} min (avg: {avg_min:.1f} min/file)")
                print()
            
            print(f"📈 Total: {total_files} files, {total_duration:.1f} minutes")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Could not retrieve stats: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Telugu-English Q&A System for Audio Transcripts"
    )
    parser.add_argument(
        "--question",
        help="Ask a specific question (non-interactive mode)"
    )
    parser.add_argument(
        "--language",
        choices=['te', 'en', 'hi', 'all'],
        help="Filter results by language"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show language statistics and exit"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Show list of all processed audio files and exit"
    )
    
    args = parser.parse_args()
    
    qa = TeluguEnglishQA()
    
    if args.stats:
        qa.show_language_stats()
        return
    
    if args.list:
        qa.show_audio_list()
        return
    
    if args.question:
        # Non-interactive mode
        answer = qa.ask_multilingual_question(args.question, args.language)
        print(f"Answer: {answer}")
    else:
        # Interactive mode
        qa.interactive_session()


if __name__ == "__main__":
    main()