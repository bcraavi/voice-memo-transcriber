# Quick Start Guide

## Prerequisites

- Python 3.9+ (Python 3.11-3.12 recommended)
- macOS with Apple Silicon (M1/M2/M3) or Intel Mac
- 16GB RAM recommended
- ~4GB disk space for models
- Ollama with `gemma3:4b` model

## Installation

1. **Create virtual environment and install dependencies** (choose one method):

   **Option A: Using requirements.txt (Recommended)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

   **Option B: Using the install script**
   ```bash
   ./utilities/install_deps.sh
   source venv/bin/activate
   ```

   **Option C: Manual installation**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Upgrade pip
   pip install --upgrade pip
   
   # Install core packages
   pip install numpy torch torchvision torchaudio
   pip install openai-whisper
   pip install "pyannote.audio>=3.1.0"
   pip install chromadb langchain langchain-community
   pip install webrtcvad librosa scikit-learn pydub
   ```

2. **Set up HuggingFace token**:
   ```bash
   cp .env.example .env
   # Edit .env and add your HuggingFace token
   ```

3. **Verify Ollama is ready**:
   ```bash
   ollama list  # Should show gemma3:4b
   ```

## Testing the Application

1. **Process Voice Memos** (macOS only):
   ```bash
   python utilities/voice_memos_import.py
   ```
   This will automatically find and process your Voice Memos.
   
   **Note**: If using an IDE, grant it **Full Disk Access** in System Preferences → Security & Privacy → Privacy → Full Disk Access to access Voice Memos files.

2. **Test with your own audio file**:
   ```bash
   # Using transcribe.py
   python transcribe.py --audio_file "path/to/your/audio.wav"
   
   # Using clean interface (recommended - no telemetry messages)
   python qa.py --audio_file "path/to/your/audio.wav"
   ```
   
   **First run notes:**
   - Downloads Whisper large model (~3.1GB)
   - Downloads PyAnnote speaker-diarization-3.1 (~500MB)
   - Requires 2-3GB RAM during processing

3. **Ask questions about the transcript**:
   ```bash
   # Using transcribe.py
   python transcribe.py --qa
   
   # Using clean interface (recommended)
   python qa.py
   ```

4. **View all transcripts**:
   ```bash
   python utilities/view_transcripts.py
   ```

## Troubleshooting

### If you get import errors:

1. Make sure you're in the virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Try installing missing packages individually:
   ```bash
   pip install [package_name]
   ```

### If model downloads fail:

1. **Whisper model issues**:
   ```bash
   pip install --no-cache-dir openai-whisper
   ```

2. **PyAnnote model issues**:
   ```bash
   # Check if PyAnnote is properly installed
   python -c "from pyannote.audio import Pipeline; print('✅ PyAnnote working')"
   
   # If it fails, try reinstalling
   pip uninstall pyannote.audio
   pip install "pyannote.audio>=3.1.0"
   ```

3. **Memory issues during processing**:
   - Close other applications
   - Consider using smaller models by changing `WHISPER_MODEL` to "medium" or "small"

### For Python 3.13 compatibility issues:

Consider using Python 3.11 or 3.12:
```bash
# Using homebrew
brew install python@3.11
python3.11 -m venv venv
```

## Quick Test

Verify everything is working:
```bash
# Test PyAnnote integration
python -c "from transcribe import AudioTranscriptionPipeline; print('✅ All models loaded successfully!')"

# Process a sample (if you have one)
python transcribe.py --audio_file "test.wav"

# View existing transcripts
python utilities/view_transcripts.py
```

## Model Information

**Current Configuration:**
- **Whisper**: "large" model (3.1GB, best accuracy)
- **PyAnnote**: speaker-diarization-3.1 (500MB, professional-grade)
- **Gemma3**: 4B local LLM for Q&A

**Total disk space**: ~4GB for all models
**RAM usage**: ~2-3GB during processing