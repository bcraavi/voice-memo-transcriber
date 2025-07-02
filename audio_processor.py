#!/usr/bin/env python3
"""
Audio preprocessing utilities for the transcription pipeline.
Handles audio normalization, noise reduction, and segmentation.
"""

import os
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
import librosa
import soundfile as sf
from pydub import AudioSegment
from pydub.effects import normalize
import noisereduce as nr
from tqdm import tqdm
import tempfile


def preprocess_audio(
    input_path: str, 
    output_path: Optional[str] = None,
    normalize_audio: bool = True,
    reduce_noise: bool = True
) -> str:
    """Preprocess audio file: normalize volume and reduce noise.
    
    Args:
        input_path: Path to input audio file
        output_path: Path for processed audio (optional)
        normalize_audio: Whether to normalize audio volume
        reduce_noise: Whether to apply noise reduction
        
    Returns:
        Path to processed audio file
    """
    if output_path is None:
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f"processed_{Path(input_path).name}")
    
    print(f"Preprocessing audio: {input_path}")
    
    # Load audio
    audio, sr = librosa.load(input_path, sr=None)
    
    # Reduce noise if requested
    if reduce_noise:
        print("Applying noise reduction...")
        audio = nr.reduce_noise(y=audio, sr=sr)
    
    # Save temporary WAV for pydub processing
    temp_wav = output_path.replace(Path(output_path).suffix, '_temp.wav')
    sf.write(temp_wav, audio, sr)
    
    # Load with pydub for normalization
    audio_segment = AudioSegment.from_wav(temp_wav)
    
    # Normalize if requested
    if normalize_audio:
        print("Normalizing audio volume...")
        audio_segment = normalize(audio_segment)
    
    # Export final audio
    audio_segment.export(output_path, format="wav")
    
    # Clean up temp file
    if os.path.exists(temp_wav):
        os.remove(temp_wav)
    
    print(f"Preprocessed audio saved to: {output_path}")
    return output_path


def segment_audio(
    audio_path: str,
    segment_length_minutes: float = 5.0,
    overlap_seconds: float = 10.0
) -> List[Tuple[str, float, float]]:
    """Segment audio file into smaller chunks with optional overlap.
    
    Args:
        audio_path: Path to audio file
        segment_length_minutes: Length of each segment in minutes
        overlap_seconds: Overlap between segments in seconds
        
    Returns:
        List of tuples (segment_path, start_time, end_time)
    """
    print(f"Segmenting audio into {segment_length_minutes}-minute chunks...")
    
    # Load audio
    audio = AudioSegment.from_file(audio_path)
    audio_length_ms = len(audio)
    segment_length_ms = int(segment_length_minutes * 60 * 1000)
    overlap_ms = int(overlap_seconds * 1000)
    
    segments = []
    temp_dir = tempfile.mkdtemp(prefix="audio_segments_")
    
    # Calculate segments with overlap
    start_ms = 0
    segment_idx = 0
    
    with tqdm(total=audio_length_ms, desc="Creating audio segments", unit="ms") as pbar:
        while start_ms < audio_length_ms:
            # Calculate end time
            end_ms = min(start_ms + segment_length_ms, audio_length_ms)
            
            # Extract segment
            segment = audio[start_ms:end_ms]
            
            # Save segment
            segment_path = os.path.join(temp_dir, f"segment_{segment_idx:04d}.wav")
            segment.export(segment_path, format="wav")
            
            # Store segment info
            segments.append((
                segment_path,
                start_ms / 1000.0,  # Convert to seconds
                end_ms / 1000.0
            ))
            
            # Update progress
            pbar.update(end_ms - start_ms)
            
            # Move to next segment (with overlap)
            start_ms = end_ms - overlap_ms if end_ms < audio_length_ms else audio_length_ms
            segment_idx += 1
    
    print(f"Created {len(segments)} segments in {temp_dir}")
    return segments


def merge_segment_results(
    segment_results: List[List[dict]],
    segment_infos: List[Tuple[str, float, float]]
) -> List[dict]:
    """Merge results from segmented processing back into a single timeline.
    
    Args:
        segment_results: List of results for each segment
        segment_infos: List of (path, start_time, end_time) for each segment
        
    Returns:
        Merged results with adjusted timestamps
    """
    merged_results = []
    
    for segment_result, (_, segment_start, segment_end) in zip(segment_results, segment_infos):
        for item in segment_result:
            # Adjust timestamps
            adjusted_item = item.copy()
            adjusted_item['start'] += segment_start
            adjusted_item['end'] += segment_start
            
            # Only include if within segment bounds (handles overlap)
            if adjusted_item['end'] <= segment_end:
                merged_results.append(adjusted_item)
    
    # Sort by start time and remove duplicates from overlap
    merged_results.sort(key=lambda x: x['start'])
    
    # Remove duplicates (keep first occurrence)
    final_results = []
    seen_texts = set()
    
    for item in merged_results:
        text_key = (item['speaker'], item['text'], round(item['start'], 1))
        if text_key not in seen_texts:
            seen_texts.add(text_key)
            final_results.append(item)
    
    return final_results


def estimate_processing_time(audio_path: str) -> Tuple[float, str]:
    """Estimate processing time based on audio duration.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Tuple of (duration_minutes, estimated_time_string)
    """
    audio = AudioSegment.from_file(audio_path)
    duration_minutes = len(audio) / (1000 * 60)
    
    # Estimate based on ~5-10x real-time processing
    estimated_minutes = duration_minutes * 7.5  # Average of 5-10x
    
    if estimated_minutes < 60:
        time_str = f"{estimated_minutes:.0f} minutes"
    else:
        hours = estimated_minutes / 60
        time_str = f"{hours:.1f} hours"
    
    return duration_minutes, time_str


def cleanup_segments(segment_paths: List[str]):
    """Clean up temporary segment files.
    
    Args:
        segment_paths: List of segment file paths to delete
    """
    for path in segment_paths:
        if os.path.exists(path):
            os.remove(path)
    
    # Remove temp directory if empty
    if segment_paths:
        temp_dir = os.path.dirname(segment_paths[0])
        if os.path.exists(temp_dir) and not os.listdir(temp_dir):
            os.rmdir(temp_dir)