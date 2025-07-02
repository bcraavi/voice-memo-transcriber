#!/usr/bin/env python3
"""
Audio Transcription and Speaker Diarization Pipeline
Processes audio files to create speaker-aware, searchable transcripts.
All processing happens locally without external API calls.
"""

import os
import sys
import argparse
import warnings
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import hashlib
import json
import re
import sqlite3
import torch
import whisper
import chromadb
from chromadb.config import Settings
import os
# Disable ChromaDB telemetry to avoid errors
os.environ["ANONYMIZED_TELEMETRY"] = "False"
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain.chains import RetrievalQA
import librosa
import soundfile as sf
import numpy as np
from pyannote.audio import Pipeline
from tqdm import tqdm
from audio_processor import preprocess_audio, segment_audio, merge_segment_results, estimate_processing_time, cleanup_segments

warnings.filterwarnings("ignore")

# Constants
WHISPER_MODEL = "large"
OLLAMA_MODEL = "gemma3:4b"
CHROMA_PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "audio_transcripts"
METADATA_DB = "transcripts_metadata.db"


class PyAnnoteSpeakerDiarization:
    """PyAnnote speaker diarization using speaker-diarization-3.1."""
    
    def __init__(self):
        print("Loading PyAnnote speaker-diarization-3.1 model...")
        
        # Load HF token from environment or .env file
        import os
        from dotenv import load_dotenv
        load_dotenv()
        hf_token = os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_ACCESS_TOKEN')
        
        if not hf_token:
            raise ValueError(
                "PyAnnote speaker-diarization-3.1 requires authentication.\n"
                "1. Accept license at: https://huggingface.co/pyannote/speaker-diarization-3.1\n"
                "2. Get token at: https://huggingface.co/settings/tokens\n"
                "3. Add HF_TOKEN=your_token to .env file"
            )
        
        # Load the speaker-diarization-3.1 pipeline
        try:
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=hf_token
            )
            if self.pipeline is None:
                raise ValueError("Pipeline loaded as None - authentication may have failed")
            print("✓ PyAnnote speaker-diarization-3.1 loaded successfully")
        except Exception as e:
            raise ValueError(f"Failed to load PyAnnote pipeline: {e}")
        
        # Send to GPU if available (MPS for Apple Silicon)
        import torch
        if self.pipeline is not None:
            if torch.backends.mps.is_available():
                self.pipeline.to(torch.device("mps"))
                print("✓ PyAnnote model running on Apple Silicon GPU (MPS)")
            elif torch.cuda.is_available():
                self.pipeline.to(torch.device("cuda"))
                print("✓ PyAnnote model running on CUDA GPU")
            else:
                print("✓ PyAnnote model running on CPU")
        
    def extract_speaker_embeddings(self, audio_path: str) -> Tuple[np.ndarray, List[Tuple[float, float]]]:
        """Extract speaker segments using PyAnnote speaker-diarization-3.1.
        
        Returns:
            embeddings: numpy array of speaker embeddings
            segments: list of (start, end) time tuples for each segment
        """
        return self._extract_with_pyannote(audio_path)
    
    def _extract_with_pyannote(self, audio_path: str) -> Tuple[np.ndarray, List[Tuple[float, float]]]:
        """Extract speaker segments using PyAnnote speaker-diarization-3.1."""
        # Pre-load audio for faster processing
        import torchaudio
        try:
            waveform, sample_rate = torchaudio.load(audio_path)
            # Run diarization with progress monitoring
            from pyannote.audio.pipelines.utils.hook import ProgressHook
            with ProgressHook() as hook:
                diarization = self.pipeline(
                    {"waveform": waveform, "sample_rate": sample_rate},
                    hook=hook
                )
        except Exception:
            # Fallback to file path
            diarization = self.pipeline(audio_path)
        
        # Convert to our format
        segments = []
        speaker_labels = []
        
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append((turn.start, turn.end))
            speaker_labels.append(speaker)
        
        if not segments:
            raise ValueError("No speech segments found in audio file")
        
        # Create embeddings (using speaker labels as simple embeddings)
        unique_speakers = list(set(speaker_labels))
        speaker_to_id = {speaker: i for i, speaker in enumerate(unique_speakers)}
        
        embeddings = []
        for speaker in speaker_labels:
            # Create one-hot encoding as embedding
            embedding = np.zeros(len(unique_speakers))
            embedding[speaker_to_id[speaker]] = 1.0
            embeddings.append(embedding)
        
        print(f"✓ PyAnnote identified {len(unique_speakers)} speakers in {len(segments)} segments")
        return np.array(embeddings), segments


class AudioTranscriptionPipeline:
    def __init__(self):
        """Initialize the audio transcription pipeline."""
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Initialize models
        self._init_models()
        
    def _init_models(self):
        """Initialize Whisper and diarization models."""
        print("Loading Whisper model...")
        self.whisper_model = whisper.load_model(WHISPER_MODEL)
        
        print("Initializing PyAnnote speaker diarization...")
        self.diarizer = PyAnnoteSpeakerDiarization()
        
    def diarize_audio(self, audio_path: str) -> List[Dict]:
        """Perform speaker diarization on the audio file.
        
        Returns:
            List of diarization segments with speaker labels
        """
        print("Starting speaker diarization...")
        
        # Extract embeddings and segments - PyAnnote already provides speaker labels
        with tqdm(total=1, desc="Running speaker diarization", unit="task") as pbar:
            embeddings, segments = self.diarizer.extract_speaker_embeddings(audio_path)
            pbar.update(1)
        
        if len(embeddings) == 0:
            print("No speech segments detected.")
            return []
        
        # Convert segments to our format - speaker info is already in embeddings
        diarization_results = []
        for i, (start, end) in tqdm(enumerate(segments), total=len(segments), desc="Processing speaker segments"):
            # Find the speaker with highest confidence (max value in embedding)
            speaker_id = np.argmax(embeddings[i])
            diarization_results.append({
                'start': start,
                'end': end,
                'speaker': f'Speaker_{speaker_id + 1}'
            })
        
        # Print diarization results
        print("\nDiarization results:")
        for segment in diarization_results[:10]:  # Show first 10 segments
            print(f"{segment['speaker']}: {segment['start']:.1f}s - {segment['end']:.1f}s")
        
        if len(diarization_results) > 10:
            print(f"... and {len(diarization_results) - 10} more segments")
        
        return diarization_results
        
    def transcribe_audio(self, audio_path: str, language: str = None) -> Dict:
        """Transcribe audio using Whisper with language detection.
        
        Args:
            audio_path: Path to the audio file
            language: Language code (e.g., 'en', 'es', 'fr') or None for auto-detection
            
        Returns:
            Transcription result with timestamps and detected language
        """
        print("\nStarting transcription...")
        with tqdm(total=1, desc="Transcribing with Whisper", unit="task") as pbar:
            if language and language != "auto":
                # Use specified language
                result = self.whisper_model.transcribe(
                    audio_path,
                    language=language,
                    word_timestamps=True
                )
            else:
                # Auto-detect language
                result = self.whisper_model.transcribe(
                    audio_path,
                    word_timestamps=True
                )
            pbar.update(1)
        
        detected_language = result.get("language", "en")
        print(f"Transcription complete. Detected language: {detected_language}")
        return result
        
    def align_transcript_with_speakers(
        self, 
        transcription: Dict, 
        diarization: List[Dict]
    ) -> List[Dict]:
        """Align transcribed text with speaker labels.
        
        Args:
            transcription: Whisper transcription result
            diarization: Diarization results
            
        Returns:
            List of segments with speaker, text, and timestamp
        """
        print("\nAligning transcript with speakers...")
        aligned_segments = []
        
        # Extract segments from transcription
        segments = transcription.get("segments", [])
        for segment in tqdm(segments, desc="Aligning speakers with text"):
            start_time = segment["start"]
            end_time = segment["end"]
            text = segment["text"].strip()
            
            if not text:
                continue
                
            # Find the speaker at this timestamp
            speaker = self._get_speaker_at_time(diarization, start_time, end_time)
            
            aligned_segments.append({
                "speaker": speaker,
                "text": text,
                "start": start_time,
                "end": end_time
            })
            
        print(f"Created {len(aligned_segments)} aligned segments.")
        return aligned_segments
        
    def _get_speaker_at_time(
        self, 
        diarization: List[Dict], 
        start: float, 
        end: float
    ) -> str:
        """Find the most likely speaker for a given time segment.
        
        Args:
            diarization: Diarization results
            start: Start time in seconds
            end: End time in seconds
            
        Returns:
            Speaker label
        """
        # Find overlapping speaker segments
        overlaps = {}
        
        for segment in diarization:
            seg_start = segment['start']
            seg_end = segment['end']
            speaker = segment['speaker']
            
            # Calculate overlap
            overlap_start = max(start, seg_start)
            overlap_end = min(end, seg_end)
            overlap_duration = max(0, overlap_end - overlap_start)
            
            if overlap_duration > 0:
                if speaker not in overlaps:
                    overlaps[speaker] = 0
                overlaps[speaker] += overlap_duration
                
        # Return speaker with maximum overlap
        if overlaps:
            return max(overlaps, key=overlaps.get)
        return "Unknown"
        
    def store_in_chromadb(
        self, 
        segments: List[Dict], 
        audio_filename: str,
        audio_path: str = None,
        language: str = "en"
    ) -> chromadb.Collection:
        """Store transcript segments in ChromaDB.
        
        Args:
            segments: List of aligned transcript segments
            audio_filename: Name of the source audio file
            
        Returns:
            ChromaDB collection
        """
        print("\nStoring segments in database...")
        
        # Initialize ChromaDB client with telemetry disabled
        client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # Prepare documents for storage
        documents = []
        metadatas = []
        ids = []
        
        # Calculate file hash if path provided
        file_hash = get_file_hash(audio_path) if audio_path else "unknown"
        
        for i, segment in enumerate(segments):
            doc_id = f"{audio_filename}_{i}"
            
            # Create document text with speaker info
            doc_text = f"[{segment['speaker']}]: {segment['text']}"
            documents.append(doc_text)
            
            # Store metadata
            metadatas.append({
                "speaker": segment["speaker"],
                "start_time": segment["start"],
                "end_time": segment["end"],
                "audio_file": audio_filename,
                "file_hash": file_hash,
                "language": language
            })
            
            ids.append(doc_id)
            
        # Add to collection
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"Stored {len(documents)} segments in ChromaDB.")
        return collection


class TranscriptQA:
    def __init__(self):
        """Initialize the Q&A system."""
        self.llm = Ollama(model=OLLAMA_MODEL)
        
        # Initialize ChromaDB client with telemetry disabled
        client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get the collection directly from ChromaDB
        self.collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        # For langchain compatibility, we'll use a simple approach
        self.vectorstore = None
        
    def ask_question(self, question: str) -> str:
        """Ask a question about the transcripts.
        
        Args:
            question: User's question
            
        Returns:
            Answer from the LLM
        """
        import time
        import threading
        import sys
        
        start_time = time.time()
        
        # Animation for searching
        def search_animation():
            chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
            idx = 0
            while not stop_animation:
                elapsed = time.time() - start_time
                sys.stdout.write(f"\r🔍 Searching transcript database {chars[idx % len(chars)]} ({elapsed:.1f}s)")
                sys.stdout.flush()
                time.sleep(0.1)
                idx += 1
        
        stop_animation = False
        search_thread = threading.Thread(target=search_animation)
        search_thread.daemon = True
        search_thread.start()
        
        try:
            # Query ChromaDB directly
            results = self.collection.query(
                query_texts=[question],
                n_results=10
            )
            
            # Stop search animation
            stop_animation = True
            search_thread.join(timeout=0.1)
            search_elapsed = time.time() - start_time
            sys.stdout.write(f"\r🔍 Database search completed in {search_elapsed:.1f}s\n")
            sys.stdout.flush()
            
            if not results['documents'][0]:
                return "No relevant transcript segments found. Please process some audio files first."
            
            # Print source segments
            print("\nRelevant transcript segments:")
            documents = results['documents'][0]
            metadatas = results['metadatas'][0] if results['metadatas'] else [{}] * len(documents)
            
            for doc, metadata in zip(documents, metadatas):
                print(f"- {doc}")
                if metadata:
                    print(f"  (File: {metadata.get('audio_file', 'Unknown')}, "
                          f"Time: {metadata.get('start_time', 0):.1f}s - "
                          f"{metadata.get('end_time', 0):.1f}s)")
            
            # Create context for LLM
            context = "\n".join(documents)
            
            # Animation for LLM processing
            def llm_animation():
                chars = "🤖💭🧠⚡🔮💡🎯🚀"
                idx = 0
                while not stop_llm_animation:
                    elapsed = time.time() - llm_start_time
                    sys.stdout.write(f"\r{chars[idx % len(chars)]} Gemma3 is thinking... ({elapsed:.1f}s)")
                    sys.stdout.flush()
                    time.sleep(1.5)
                    idx += 1
            
            llm_start_time = time.time()
            stop_llm_animation = False
            llm_thread = threading.Thread(target=llm_animation)
            llm_thread.daemon = True
            llm_thread.start()
            
            # Generate answer using Ollama with better prompting
            prompt = f"""You are an intelligent assistant helping to analyze audio transcripts. Please provide a helpful, detailed response to the user's question based on the transcript content.

User Question: {question}

Transcript Content:
{context}

Instructions:
- If the transcript is in Telugu, provide translation to English when relevant
- Give detailed, conversational responses
- Include specific details from the transcript
- If asked to translate, provide accurate English translations
- Be helpful and thorough in your analysis

Response:"""
            
            answer = self.llm.invoke(prompt)
            
            # Stop LLM animation
            stop_llm_animation = True
            llm_thread.join(timeout=0.1)
            llm_elapsed = time.time() - llm_start_time
            total_elapsed = time.time() - start_time
            sys.stdout.write(f"\r🎉 Response generated in {llm_elapsed:.1f}s (Total: {total_elapsed:.1f}s)\n")
            sys.stdout.flush()
            
            return answer
            
        except Exception as e:
            # Stop any running animations
            stop_animation = True
            if 'stop_llm_animation' in locals():
                stop_llm_animation = True
            return f"Error searching transcripts: {e}"
        finally:
            # Ensure animations are stopped
            if 'stop_animation' in locals():
                stop_animation = True
            if 'stop_llm_animation' in locals():
                stop_llm_animation = True


def get_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hex digest of the file hash
    """
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def is_file_processed(audio_path: str, collection) -> bool:
    """Check if a file has already been processed.
    
    Args:
        audio_path: Path to the audio file
        collection: ChromaDB collection
        
    Returns:
        True if file is already processed, False otherwise
    """
    file_hash = get_file_hash(audio_path)
    results = collection.get(where={"file_hash": file_hash})
    return len(results['ids']) > 0


def init_metadata_db():
    """Initialize SQLite database for storing file metadata."""
    conn = sqlite3.connect(METADATA_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_metadata (
            file_hash TEXT PRIMARY KEY,
            original_path TEXT,
            new_path TEXT,
            title TEXT,
            language TEXT,
            duration_seconds REAL,
            processed_date TEXT,
            summary TEXT
        )
    """)
    conn.commit()
    return conn


def generate_content_title(transcript_text: str, language: str = "en") -> str:
    """Generate a descriptive title from transcript content using Ollama.
    
    Args:
        transcript_text: The transcript text to summarize
        language: Language code of the transcript
        
    Returns:
        A sanitized title suitable for file naming
    """
    try:
        llm = Ollama(model=OLLAMA_MODEL)
        
        # Limit transcript to first 2000 chars for title generation
        sample_text = transcript_text[:2000]
        
        # Create language-aware prompt
        if language != "en":
            prompt = f"""Generate a concise 5-10 word title for this {language} audio transcript. 
            The title should capture the main topic or theme. Reply with ONLY the title, no explanation.
            
            Transcript: {sample_text}"""
        else:
            prompt = f"""Generate a concise 5-10 word title for this audio transcript. 
            The title should capture the main topic or theme. Reply with ONLY the title, no explanation.
            
            Transcript: {sample_text}"""
        
        title = llm.invoke(prompt).strip()
        
        # Sanitize title for file system
        # Remove special characters, keep alphanumeric, spaces, and hyphens
        title = re.sub(r'[^\w\s-]', '', title)
        title = re.sub(r'[-\s]+', '_', title)  # Replace spaces/hyphens with underscores
        title = title.strip('_')[:60]  # Limit length to 60 chars
        
        return title if title else "untitled_transcript"
        
    except Exception as e:
        print(f"Error generating title: {e}")
        return "untitled_transcript"


def rename_audio_file(original_path: str, new_title: str, preserve_original: bool = True) -> str:
    """Rename audio file based on generated title.
    
    Args:
        original_path: Original file path
        new_title: New title for the file
        preserve_original: Whether to copy instead of rename
        
    Returns:
        Path to the renamed/copied file
    """
    original_dir = os.path.dirname(original_path)
    original_ext = Path(original_path).suffix
    
    # Create new filename
    new_filename = f"{new_title}{original_ext}"
    new_path = os.path.join(original_dir, new_filename)
    
    # Handle duplicates
    if os.path.exists(new_path) and new_path != original_path:
        counter = 1
        while os.path.exists(os.path.join(original_dir, f"{new_title}_{counter}{original_ext}")):
            counter += 1
        new_filename = f"{new_title}_{counter}{original_ext}"
        new_path = os.path.join(original_dir, new_filename)
    
    # Rename or copy file
    if preserve_original:
        import shutil
        shutil.copy2(original_path, new_path)
        print(f"Copied to: {new_filename}")
    else:
        os.rename(original_path, new_path)
        print(f"Renamed to: {new_filename}")
    
    return new_path


def save_file_metadata(
    conn: sqlite3.Connection,
    file_hash: str,
    original_path: str,
    new_path: str,
    title: str,
    language: str,
    duration_seconds: float,
    summary: str = ""
):
    """Save file metadata to SQLite database."""
    cursor = conn.cursor()
    from datetime import datetime
    
    cursor.execute("""
        INSERT OR REPLACE INTO file_metadata 
        (file_hash, original_path, new_path, title, language, duration_seconds, processed_date, summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        file_hash,
        original_path,
        new_path,
        title,
        language,
        duration_seconds,
        datetime.now().isoformat(),
        summary
    ))
    conn.commit()


def process_audio_file_segmented(
    audio_path: str, 
    segment_length_minutes: float = 5.0,
    preprocess: bool = False,
    skip_processed: bool = True,
    language: str = None,
    rename_file: bool = False,
    preserve_original: bool = True
):
    """Process a long audio file in segments to manage memory usage.
    
    Args:
        audio_path: Path to the audio file
        segment_length_minutes: Length of each segment in minutes
        preprocess: Whether to preprocess audio
        skip_processed: Whether to skip already processed files
    """
    # Validate file exists
    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found: {audio_path}")
        return
    
    print(f"Processing audio file in segments: {audio_path}")
    
    # Check if already processed
    if skip_processed:
        file_hash = get_file_hash(audio_path)
        pipeline = AudioTranscriptionPipeline()
        try:
            results = pipeline.collection.get(where={"file_hash": file_hash})
            if len(results['ids']) > 0:
                print(f"✓ File already processed (hash: {file_hash[:8]}...). Skipping.")
                return
        except:
            pass
    
    # Estimate processing time
    duration_minutes, time_estimate = estimate_processing_time(audio_path)
    print(f"Audio duration: {duration_minutes:.1f} minutes")
    print(f"Estimated processing time: {time_estimate}")
    
    # Preprocess if requested
    processed_audio_path = audio_path
    if preprocess:
        print("\nPreprocessing audio...")
        processed_audio_path = preprocess_audio(audio_path)
    
    # Segment audio
    segments = segment_audio(processed_audio_path, segment_length_minutes)
    print(f"\nProcessing {len(segments)} segments...")
    
    # Initialize pipeline
    pipeline = AudioTranscriptionPipeline()
    audio_filename = Path(audio_path).name
    
    # Process each segment
    all_aligned_segments = []
    for i, (segment_path, start_time, end_time) in enumerate(tqdm(segments, desc="Processing segments")):
        print(f"\n--- Segment {i+1}/{len(segments)} ({start_time:.1f}s - {end_time:.1f}s) ---")
        
        # Diarization
        diarization = pipeline.diarize_audio(segment_path)
        
        # Transcription with language support
        transcription = pipeline.transcribe_audio(segment_path, language=language)
        if i == 0:  # Get language from first segment
            detected_language = transcription.get("language", "en")
        
        # Align
        if diarization:
            aligned = pipeline.align_transcript_with_speakers(transcription, diarization)
        else:
            aligned = []
            for segment in transcription.get("segments", []):
                if segment["text"].strip():
                    aligned.append({
                        "speaker": "Speaker_1",
                        "text": segment["text"].strip(),
                        "start": segment["start"],
                        "end": segment["end"]
                    })
        
        all_aligned_segments.append(aligned)
    
    # Merge results
    print("\nMerging segment results...")
    merged_segments = merge_segment_results(all_aligned_segments, segments)
    
    # Store in ChromaDB with language metadata
    collection = pipeline.store_in_chromadb(merged_segments, audio_filename, audio_path, language=detected_language)
    
    # Generate content-based title and rename if requested
    new_path = audio_path
    if rename_file:
        # Get full transcript text
        transcript_text = " ".join(segment["text"] for segment in merged_segments)
        
        # Generate title
        print("\nGenerating content-based title...")
        title = generate_content_title(transcript_text, detected_language)
        
        # Rename file
        new_path = rename_audio_file(audio_path, title, preserve_original)
    
    # Store metadata in SQLite
    metadata_conn = init_metadata_db()
    file_hash = get_file_hash(audio_path)
    
    # Save metadata
    save_file_metadata(
        metadata_conn,
        file_hash,
        audio_path,
        new_path,
        title if rename_file else Path(audio_path).stem,
        detected_language,
        duration_minutes * 60  # Convert to seconds
    )
    metadata_conn.close()
    
    # Cleanup
    cleanup_segments([s[0] for s in segments])
    if preprocess and processed_audio_path != audio_path:
        os.remove(processed_audio_path)
    
    print("\n✅ Segmented audio processing complete!")
    print(f"Transcript stored in ChromaDB collection: {COLLECTION_NAME}")
    print(f"Language: {detected_language}")
    if rename_file:
        print(f"File renamed to: {Path(new_path).name}")
    
    # Print sample segments
    print("\nSample transcript segments:")
    for segment in merged_segments[:5]:
        print(f"[{segment['speaker']}] ({segment['start']:.1f}s): {segment['text']}")


def process_audio_file(
    audio_path: str, 
    skip_processed: bool = True,
    language: str = None,
    rename_file: bool = False,
    preserve_original: bool = True
):
    """Process a single audio file through the complete pipeline.
    
    Args:
        audio_path: Path to the audio file
        skip_processed: Whether to skip already processed files
        language: Language code for transcription (None for auto-detection)
        rename_file: Whether to rename file based on content
        preserve_original: Whether to preserve original file when renaming
    """
    # Validate file exists
    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found: {audio_path}")
        return
        
    print(f"Processing audio file: {audio_path}")
    
    # Initialize pipeline
    pipeline = AudioTranscriptionPipeline()
    
    # Get filename for storage
    audio_filename = Path(audio_path).name
    
    # Check if file already processed
    if skip_processed:
        file_hash = get_file_hash(audio_path)
        try:
            results = pipeline.collection.get(where={"file_hash": file_hash})
            if len(results['ids']) > 0:
                print(f"✓ File already processed (hash: {file_hash[:8]}...). Skipping.")
                return
        except:
            pass  # Continue if collection doesn't exist yet
    
    # Step 1: Diarization
    diarization = pipeline.diarize_audio(audio_path)
    
    if not diarization:
        print("No speakers detected. Proceeding with transcription only.")
    
    # Step 2: Transcription with language support
    transcription = pipeline.transcribe_audio(audio_path, language=language)
    detected_language = transcription.get("language", "en")
    
    # Step 3: Align transcript with speakers
    if diarization:
        aligned_segments = pipeline.align_transcript_with_speakers(
            transcription, diarization
        )
    else:
        # Create segments without speaker labels
        aligned_segments = []
        for segment in transcription.get("segments", []):
            if segment["text"].strip():
                aligned_segments.append({
                    "speaker": "Speaker_1",
                    "text": segment["text"].strip(),
                    "start": segment["start"],
                    "end": segment["end"]
                })
    
    # Step 4: Store in ChromaDB with language metadata
    collection = pipeline.store_in_chromadb(aligned_segments, audio_filename, audio_path, language=detected_language)
    
    # Step 5: Generate content-based title and rename if requested
    new_path = audio_path
    if rename_file:
        # Get full transcript text
        transcript_text = " ".join(segment["text"] for segment in aligned_segments)
        
        # Generate title
        print("\nGenerating content-based title...")
        title = generate_content_title(transcript_text, detected_language)
        
        # Rename file
        new_path = rename_audio_file(audio_path, title, preserve_original)
    
    # Step 6: Store metadata in SQLite
    metadata_conn = init_metadata_db()
    file_hash = get_file_hash(audio_path)
    
    # Calculate audio duration
    from pydub import AudioSegment
    audio = AudioSegment.from_file(audio_path)
    duration_seconds = len(audio) / 1000.0
    
    # Save metadata
    save_file_metadata(
        metadata_conn,
        file_hash,
        audio_path,
        new_path,
        title if rename_file else Path(audio_path).stem,
        detected_language,
        duration_seconds
    )
    metadata_conn.close()
    
    print("\n✅ Audio processing complete!")
    print(f"Transcript stored in ChromaDB collection: {COLLECTION_NAME}")
    print(f"Language: {detected_language}")
    if rename_file:
        print(f"File renamed to: {Path(new_path).name}")
    
    # Print sample segments
    print("\nSample transcript segments:")
    for segment in aligned_segments[:5]:
        print(f"[{segment['speaker']}] ({segment['start']:.1f}s): {segment['text']}")


def interactive_qa():
    """Run interactive Q&A session."""
    print("\n=== Interactive Q&A Mode ===")
    print("Type 'quit' to exit\n")
    
    qa_system = TranscriptQA()
    
    while True:
        question = input("\nYour question: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            break
            
        if not question:
            print("Please enter a question.")
            continue
            
        try:
            answer = qa_system.ask_question(question)
            print(f"\nAnswer: {answer}")
        except Exception as e:
            print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Process audio files for speaker-aware transcription"
    )
    parser.add_argument(
        "--audio_file",
        type=str,
        help="Path to the audio file to process"
    )
    parser.add_argument(
        "--qa",
        action="store_true",
        help="Start interactive Q&A mode"
    )
    parser.add_argument(
        "--segment",
        action="store_true",
        help="Process long audio files in segments (recommended for files > 30 minutes)"
    )
    parser.add_argument(
        "--segment_length",
        type=float,
        default=5.0,
        help="Length of each segment in minutes (default: 5.0)"
    )
    parser.add_argument(
        "--preprocess",
        action="store_true",
        help="Preprocess audio (normalize volume and reduce noise)"
    )
    parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="Language code for transcription (e.g., en, es, fr, zh, ja) or 'auto' for detection"
    )
    parser.add_argument(
        "--rename",
        action="store_true",
        help="Rename audio file based on transcript content"
    )
    parser.add_argument(
        "--preserve_original",
        action="store_true",
        default=True,
        help="Preserve original file when renaming (create a copy)"
    )
    
    args = parser.parse_args()
    
    # Process audio file if provided
    if args.audio_file:
        if args.segment:
            process_audio_file_segmented(
                args.audio_file, 
                segment_length_minutes=args.segment_length,
                preprocess=args.preprocess,
                language=args.language,
                rename_file=args.rename,
                preserve_original=args.preserve_original
            )
        else:
            process_audio_file(
                args.audio_file,
                language=args.language,
                rename_file=args.rename,
                preserve_original=args.preserve_original
            )
    
    # Start Q&A mode if requested
    if args.qa or not args.audio_file:
        interactive_qa()


if __name__ == "__main__":
    main()