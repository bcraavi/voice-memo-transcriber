#!/bin/bash
# Setup script for daily automation

echo "🔧 Setting up daily automation for Audio Transcriber..."

# Get the parent directory (main Audio transcriber directory)
PARENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Update paths in the plist file - use parent directory for base path
sed -i '' "s|/Users/banvithchowdaryravi/Code base/Audio transcriber|$PARENT_DIR|g" "$SCRIPT_DIR/com.audiotranscriber.auto.plist"

# Copy plist to LaunchAgents
PLIST_DEST="$HOME/Library/LaunchAgents/com.audiotranscriber.auto.plist"
cp "$SCRIPT_DIR/com.audiotranscriber.auto.plist" "$PLIST_DEST"

# Load the launch agent
launchctl load "$PLIST_DEST"

echo "✅ Automation setup complete!"
echo ""
echo "📋 The transcriber will run every 30 minutes automatically"
echo ""
echo "🛠️  To manage the automation:"
echo "  • Check status: launchctl list | grep audiotranscriber"
echo "  • Stop automation: launchctl unload ~/Library/LaunchAgents/com.audiotranscriber.auto.plist"
echo "  • Start automation: launchctl load ~/Library/LaunchAgents/com.audiotranscriber.auto.plist"
echo "  • Run manually: ./automation/auto_transcribe.sh"
echo ""
echo "📝 Logs will be saved in: $PARENT_DIR/logs/"
echo ""
echo "⚠️  Note: Notifications are disabled for 30-min runs to avoid spam"