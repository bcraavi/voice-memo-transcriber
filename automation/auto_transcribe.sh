#!/bin/bash
# Automated Transcription Script
# Processes new audio files every 30 minutes automatically

# Set the path to your Audio transcriber directory (parent of automation/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Log file for automated runs (includes hour and minute)
LOG_FILE="logs/auto_transcribe_$(date +%Y%m%d_%H%M).log"
mkdir -p logs

echo "====================================" >> "$LOG_FILE"
echo "Auto Transcription Started: $(date)" >> "$LOG_FILE"
echo "====================================" >> "$LOG_FILE"

# Process new Voice Memos
echo "Importing new Voice Memos..." >> "$LOG_FILE"
python utilities/voice_memos_import.py >> "$LOG_FILE" 2>&1

# Process all audio files in voice_memos directory
echo "Processing audio files..." >> "$LOG_FILE"
python automation/batch_transcribe.py voice_memos --rename --segment >> "$LOG_FILE" 2>&1

# Optional: Send notification (macOS) - disabled for 30-min runs to avoid spam
# if [[ "$OSTYPE" == "darwin"* ]]; then
#     osascript -e 'display notification "Auto transcription completed" with title "Audio Transcriber"'
# fi

echo "Auto Transcription Completed: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Optional: Clean up old logs (keep last 7 days for 30-min runs)
find logs -name "auto_transcribe_*.log" -mtime +7 -delete

# Deactivate virtual environment
deactivate