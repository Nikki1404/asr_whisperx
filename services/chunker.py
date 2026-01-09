import numpy as np

def iter_chunks(audio: np.ndarray, sr: int, chunk_sec: float, stride_sec: float):
    chunk = int(chunk_sec * sr)
    stride = int(stride_sec * sr)
    hop = max(1, chunk - stride)

    i = 0
    n = len(audio)

    while i < n:
        j = min(n, i + chunk)
        yield audio[i:j], i / sr
        if j == n:
            break
        i += hop
