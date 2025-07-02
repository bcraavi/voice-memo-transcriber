# Voice Memo Transcriber

A Python application that processes audio files to create speaker-aware, searchable transcripts using state-of-the-art AI models. All processing happens locally on your machine with professional-grade accuracy. Optimized for Apple Silicon MacBooks.

## Features

- **PyAnnote Speaker Diarization**: Uses PyAnnote speaker-diarization-3.1 for professional-grade speaker identification
- **Whisper Large Model**: Uses OpenAI's Whisper "large" model for maximum transcription accuracy
- **Speaker-Aware Transcripts**: Combines advanced diarization and transcription for precise speaker-labeled text
- **Vector Database Storage**: Stores transcripts in ChromaDB for efficient searching
- **Question Answering**: Ask questions about your transcripts using RAG with local Gemma3 LLM
- **Apple Silicon Optimized**: Leverages MPS acceleration on M-series Macs
- **100% Local Processing**: No API keys required, internet only needed for initial model downloads
- **Voice Memo Support**: Direct integration with macOS Voice Memos app

## Prerequisites

- Python 3.9+ (Python 3.11-3.12 recommended for best compatibility)
- macOS with Apple Silicon (M3+)
- 16GB RAM recommended (optimal performance with 32GB)
- ~4GB disk space for models (Whisper large: 3.1GB, PyAnnote: 500MB)
- Ollama installed with `gemma3:4b` model

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/bcraavi/voice-memo-transcriber.git
cd voice-memo-transcriber
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

Choose one of these methods:

**Option A - Using pip (recommended):**
```bash
pip install -r requirements.txt
```

**Option B - Using install script:**
```bash
./utilities/install_deps.sh
```

**Note**: All dependencies install automatically, including PyAnnote speaker-diarization-3.1 and its requirements.

### 4. Set up HuggingFace token (for PyAnnote)

PyAnnote speaker-diarization-3.1 requires HuggingFace authentication:

1. **Accept the license**: Visit [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1) and accept the license
2. **Get your token**: Go to [HuggingFace Settings](https://huggingface.co/settings/tokens) and create a token
3. **Add to environment**: Copy the example file and add your token:
   ```bash
   cp .env.example .env
   # Then edit .env and replace "your_huggingface_token_here" with your actual token
   ```

### 5. Install Ollama and download the model

First, install Ollama from https://ollama.ai/

Then download the Gemma3 4B model:

```bash
ollama pull gemma3:4b
```

**Note**: For better Q&A performance, you can use larger models if you have sufficient RAM:
- `gemma3:7b` (recommended for 24GB+ RAM)
- `gemma3:12b` (recommended for 32GB+ RAM) 
- `gemma3:27b` (requires 64GB+ RAM)

To use a different model, change the `OLLAMA_MODEL` constant in `transcribe.py`.

✅ **Setup complete!** No other API keys needed.

## Usage

### Processing an Audio File

To process an audio file and create a searchable transcript:

```bash
# Using transcribe.py (supports all languages)
python transcribe.py --audio_file "path/to/your/audio.wav"

# Using clean interface (no telemetry messages)
python qa.py --audio_file "path/to/your/audio.wav"
```

**Supported formats**: `.wav`, `.mp3`, `.flac`, `.ogg` (`.m4a` requires conversion with `ffmpeg`)

The script will:
1. Load Whisper large model (~3.1GB download on first run)
2. Load PyAnnote speaker-diarization-3.1 model (~500MB download on first run)  
3. Perform professional speaker diarization (identifies multiple speakers, handles overlapping speech)
4. Generate high-accuracy transcription with speaker labels
5. Store the transcript in a local ChromaDB database
6. Show sample transcript segments when complete

**Example output**: `[Speaker_1] (2.3s): And we need to store all that data for the model.`

### Asking Questions About Your Transcripts

After processing one or more audio files, you can ask questions:

```bash
# Using transcribe.py
python transcribe.py --qa

# Using clean interface (recommended - no telemetry messages)
python qa.py

# For multilingual interface with advanced features
python qa_multilingual.py
```

This starts an interactive Q&A session where you can:
- Ask questions about the content of your transcripts
- Get answers with relevant transcript segments as context
- See which parts of which audio files were used to answer

**Q&A Interface Options:**
- `qa.py`: Simple Q&A interface with clean output (no telemetry)
- `qa_multilingual.py`: Advanced interface with:
  - Interactive commands: `list`, `stats`, `telugu`, `english`, `all`
  - File metadata viewing (duration, language, processing date)
  - Language filtering and statistics
  - Support for Telugu, English, Hindi, Tamil, and more

### Processing Multiple Files

**Option 1: Sequential Processing**
```bash
python transcribe.py --audio_file "meeting1.wav"
python transcribe.py --audio_file "meeting2.wav"
python transcribe.py --qa  # Ask questions about both meetings
```

**Option 2: Batch Processing (Recommended)**
```bash
# Process all files in a directory at once
python automation/batch_transcribe.py voice_memos

# With options
python automation/batch_transcribe.py voice_memos --rename --segment --preprocess

# Process specific directory
python automation/batch_transcribe.py /path/to/audio/files --language en
```

### Multi-Language Support (Optimized for Telugu-English)

The system automatically detects the language of your audio, with excellent support for Telugu and English:

```bash
# Auto-detect language (optimized for Telugu-English content)
python transcribe.py --audio_file "telugu_meeting.wav" --rename

# Mixed Telugu-English conversations (code-switching)
python transcribe.py --audio_file "mixed_conversation.wav" --rename

# Specify language explicitly for noisy audio
python transcribe.py --audio_file "noisy_telugu.wav" --language te --preprocess --rename

# Primary language codes for your content:
# te (Telugu - తెలుగు), en (English), hi (Hindi - occasionally)
# Also supports: ta (Tamil), kn (Kannada), ml (Malayalam), etc.
```

### Content-Based File Renaming

Automatically rename files based on their content using AI-generated titles:

```bash
# Rename file based on content (preserves original by default)
python transcribe.py --audio_file "Recording_001.wav" --rename

# Example transformations:
# "Recording_001.wav" → "Team_Meeting_Q4_Budget_Discussion.wav"
# "untitled_23.mp3" → "Interview_John_Smith_Product_Manager.mp3"
# "audio_2024_01_15.wav" → "Spanish_Lecture_Modern_Literature.wav"
```

### Processing Long Audio Files

For files longer than 30 minutes, use segmented processing:

```bash
# Process in 5-minute segments (default)
python transcribe.py --audio_file "2hour_recording.wav" --segment

# Custom segment length
python transcribe.py --audio_file "conference.mp3" --segment --segment_length 10

# With audio preprocessing (noise reduction + normalization)
python transcribe.py --audio_file "noisy_recording.wav" --segment --preprocess
```

### Advanced Usage Examples

```bash
# Spanish podcast with auto-renaming
python transcribe.py --audio_file "podcast.mp3" --language es --rename

# Long meeting with preprocessing and renaming
python transcribe.py --audio_file "board_meeting.wav" --segment --preprocess --rename

# Process without preserving original file
python transcribe.py --audio_file "temp_recording.wav" --rename --no-preserve_original
```

### Processing Voice Memos

Direct integration with macOS Voice Memos:

```bash
# Find and process your voice memos automatically
python utilities/voice_memos_import.py

# Convert .m4a voice memos to .wav if needed
ffmpeg -i "voice_memo.m4a" -ar 16000 -ac 1 "voice_memo.wav"
python transcribe.py --audio_file "voice_memo.wav"
```

**Important**: If using an IDE (VS Code, PyCharm, etc.), you need to grant **Full Disk Access** to your IDE:
1. Go to **System Preferences** → **Security & Privacy** → **Privacy** → **Full Disk Access**
2. Click the lock icon and enter your password
3. Click the **+** button and add your IDE application
4. Restart your IDE

This allows the IDE to access Voice Memos files on your behalf.

### Combined Mode

Process a file and immediately start Q&A:

```bash
python transcribe.py --audio_file "interview.mp3" --qa
```

### Viewing Processed Files Metadata

Check metadata for all processed files:

```bash
# Show all processed files with titles, languages, and dates
python utilities/view_metadata.py

# Filter by language
python utilities/view_metadata.py --language es

# Show existing transcripts (original utility)
python utilities/view_transcripts.py
```

## Example Workflow

1. **Record or obtain an audio file** (e.g., meeting, interview, podcast)

2. **Process the audio**:
   ```bash
   python transcribe.py --audio_file "team_meeting_2024.wav"
   ```

3. **Ask questions**:
   ```bash
   python transcribe.py --qa
   ```
   
   Example questions:
   - "What did John say about the project deadline?"
   - "Were there any action items discussed?"
   - "What concerns were raised during the meeting?"

## Project Structure

```
audio-transcriber/
├── transcribe.py             # Main transcription application
├── qa.py                    # Clean Q&A interface (all languages)
├── qa_multilingual.py       # Advanced multilingual Q&A with interactive features
├── audio_processor.py       # Audio preprocessing utilities
├── automation/              # Automation scripts
│   ├── batch_transcribe.py  # Batch process multiple files
│   ├── auto_transcribe.sh   # Automation script (runs every 30 min)
│   ├── setup_automation.sh  # Setup automated scheduling (macOS)
│   └── com.audiotranscriber.auto.plist  # LaunchAgent config
├── utilities/               # Utility scripts
│   ├── voice_memos_import.py  # Voice Memos integration
│   ├── voice_memos_guide.py   # Voice Memos export guide
│   ├── view_transcripts.py    # View all transcripts
│   ├── view_metadata.py       # View processed file metadata
│   ├── install_deps.sh        # Dependency installation script
│   └── workflow.sh            # Automation workflow
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── README.md              # This documentation
├── QUICKSTART.md          # Quick setup guide
├── chroma_db/             # ChromaDB storage (created automatically)
├── voice_memos/           # Audio files directory (created automatically)
├── logs/                  # Automation logs (created automatically)
└── venv/                  # Virtual environment (created automatically)
```

## Performance Tips

- **First run downloads**: Whisper large (~3.1GB) + PyAnnote (~500MB) models
- **Processing time**: ~5-10x real-time (3 min audio = 15-30 min processing) for maximum accuracy
- **Memory usage**: ~2-3GB RAM during processing (large models)
- **Apple Silicon acceleration**: Models run on GPU (MPS) for faster processing
- **Speaker separation**: PyAnnote handles overlapping speech, background noise, and multiple speakers excellently
- **Best results**: Works well with any audio quality, optimized for meetings and conversations

## Troubleshooting

### Common Issues

1. **PyAnnote authentication errors**
   - Make sure you've accepted the license at [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
   - Check your HF_TOKEN in the `.env` file
   - Get a new token from [HuggingFace Settings](https://huggingface.co/settings/tokens)

2. **"No module named 'asteroid_filterbanks'"**
   - Run: `pip install asteroid-filterbanks lightning speechbrain tensorboardX`
   - Or: `pip install -r requirements.txt` again

3. **Ollama connection errors**
   - Make sure Ollama is running: `ollama serve`
   - Verify the model is installed: `ollama list`

4. **Audio format issues**
   - Convert .m4a files: `ffmpeg -i "file.m4a" -ar 16000 -ac 1 "file.wav"`
   - Supported: .wav, .mp3, .flac, .ogg

5. **Memory issues**
   - Large models require 2-3GB RAM
   - Close other applications to free up memory
   - Excellent performance with 32GB RAM

## Advanced Configuration

You can modify constants in `transcribe.py` to customize behavior:

- `WHISPER_MODEL`: Currently "large" (best accuracy), can change to "tiny", "small", "medium"
- `OLLAMA_MODEL`: Use a different local LLM (currently gemma3:4b)
  - For better performance: `gemma3:7b`, `gemma3:12b`, `gemma3:27b`
  - Requires more RAM: 24GB+, 32GB+, 64GB+ respectively
- `CHROMA_PERSIST_DIR`: Change database location
- `COLLECTION_NAME`: Use different collections for different projects

**Note**: PyAnnote speaker-diarization-3.1 is the best available model and recommended to keep.

## Automation & Scheduling

### Automated Processing (Every 30 Minutes)

Set up automatic transcription that checks for new audio files every 30 minutes:

```bash
# One-time setup
./automation/setup_automation.sh

# The system will automatically every 30 minutes:
# - Import new Voice Memos
# - Process all new audio files
# - Log results (notifications disabled to avoid spam)
```

**Manual batch processing:**
```bash
# Process all files in voice_memos directory
python automation/batch_transcribe.py

# Process with options
python automation/batch_transcribe.py --rename --segment --preprocess

# Run automation script manually
./automation/auto_transcribe.sh
```

**Managing automation:**
```bash
# Check if running
launchctl list | grep audiotranscriber

# Stop automation
launchctl unload ~/Library/LaunchAgents/com.audiotranscriber.auto.plist

# Restart automation
launchctl load ~/Library/LaunchAgents/com.audiotranscriber.auto.plist
```

**Note**: Logs are automatically cleaned up after 7 days to save disk space.

Logs are saved in the `logs/` directory for troubleshooting.

## Privacy & Security

- **100% Local Processing**: All transcription and diarization happens on your machine
- **No Data Uploads**: Audio and transcripts never leave your computer
- **Local Storage**: ChromaDB stores everything in the `chroma_db` directory
- **Minimal Internet**: Only for initial model downloads and HuggingFace authentication

## Credits

This application uses:
- [OpenAI Whisper](https://github.com/openai/whisper) "large" model for transcription
- [PyAnnote Audio](https://github.com/pyannote/pyannote-audio) speaker-diarization-3.1 for professional speaker identification
- [ChromaDB](https://www.trychroma.com/) for vector storage and search
- [LangChain](https://langchain.com/) for RAG (Retrieval-Augmented Generation)
- [Ollama](https://ollama.ai/) with Gemma3 4B for local LLM inference

**System Status**: ✅ Fully operational with state-of-the-art models