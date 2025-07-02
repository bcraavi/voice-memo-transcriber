#!/bin/bash
# Quick workflow script for Telugu-English audio processing

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎙️  Telugu-English Audio Transcription Workflow${NC}"
echo "=================================================="

# Activate virtual environment
source venv/bin/activate

# Function to process single file
process_single() {
    echo -e "${YELLOW}Processing single file: $1${NC}"
    python main.py --audio_file "$1" --rename
}

# Function to process voice memos batch
process_batch() {
    echo -e "${YELLOW}Processing all voice memos in batch...${NC}"
    python process_voice_memos_enhanced.py
}

# Function to start Q&A
start_qa() {
    echo -e "${YELLOW}Starting Telugu-English Q&A session...${NC}"
    python telugu_english_qa.py
}

# Function to show stats
show_stats() {
    echo -e "${YELLOW}Language Statistics:${NC}"
    python telugu_english_qa.py --stats
    echo ""
    echo -e "${YELLOW}All Processed Files:${NC}"
    python show_metadata.py
}

# Main menu
if [ $# -eq 0 ]; then
    echo "Choose an option:"
    echo "1. Process single audio file"
    echo "2. Process all voice memos (batch)"
    echo "3. Start Q&A session"
    echo "4. Show statistics"
    echo "5. Quick commands help"
    echo ""
    read -p "Enter choice (1-5): " choice

    case $choice in
        1)
            read -p "Enter audio file path: " filepath
            process_single "$filepath"
            ;;
        2)
            process_batch
            ;;
        3)
            start_qa
            ;;
        4)
            show_stats
            ;;
        5)
            cat quick_commands.md
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            ;;
    esac
else
    # Command line arguments
    case $1 in
        "process")
            if [ -n "$2" ]; then
                process_single "$2"
            else
                echo -e "${RED}Please provide audio file path${NC}"
            fi
            ;;
        "batch")
            process_batch
            ;;
        "qa")
            start_qa
            ;;
        "stats")
            show_stats
            ;;
        *)
            echo "Usage: $0 [process <file>|batch|qa|stats]"
            ;;
    esac
fi