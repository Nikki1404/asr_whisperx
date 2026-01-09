# components/audio_chunking_array.py
from typing import List, Tuple
import numpy as np


def chunk_audio_array(
    audio: np.ndarray,
    chunk_sec: int = 30,
    overlap_sec: int = 2,
    sample_rate: int = 16000,
) -> List[Tuple[np.ndarray, float]]:
    """
    Chunk a 16kHz mono float32 audio array into overlapping chunks.

    Returns:
        List of (audio_chunk_array, start_offset_sec)
    """
    assert chunk_sec > overlap_sec, "chunk_sec must be > overlap_sec"

    chunk_len = int(chunk_sec * sample_rate)
    overlap_len = int(overlap_sec * sample_rate)
    step = chunk_len - overlap_len

    chunks = []
    n = len(audio)
    start = 0

    while start < n:
        end = min(start + chunk_len, n)
        chunks.append((audio[start:end], start / sample_rate))
        start += step

    return chunks
