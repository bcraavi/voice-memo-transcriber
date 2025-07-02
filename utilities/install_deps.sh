#!/bin/bash

echo "Installing dependencies for Audio Transcriber..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install core dependencies one by one
echo "Installing core dependencies..."
pip install numpy
pip install torch torchvision torchaudio
pip install openai-whisper
pip install librosa
pip install scikit-learn
pip install webrtcvad
pip install pydub

# Install database and LLM dependencies
echo "Installing database and LLM dependencies..."
pip install chromadb
pip install langchain
pip install langchain-community

# Install additional utilities
echo "Installing additional utilities..."
pip install tqdm
pip install python-dotenv
pip install accelerate

echo "Installation complete! Activate the virtual environment with:"
echo "source venv/bin/activate"