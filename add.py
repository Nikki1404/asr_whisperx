# components/audio_processing.py
import os
import time
import whisperx
from fastapi import HTTPException

from config import ALL_CONFIG
from components.logger import get_logger
from components.utils import (
    normalize_to_whisper_wav,
    get_audio_duration_sec,
    safe_remove,
)
from components.merge_speakers import TranscriptMerger
from components.post_processing_utils import post_process_itn_output
from components.whisperx_asr import get_whisperx_client
from components.audio_chunking_array import chunk_audio_array

logger = get_logger("audio-processing")
merger = TranscriptMerger()


def process_audio_file(
    file_path: str,
    asr_pipeline: str = "whisper",
    debug_enabled: bool = False,
    diarize: bool | None = None,
    min_speakers: int | None = None,
    max_speakers: int | None = None,
):
    if asr_pipeline != "whisper":
        raise HTTPException(status_code=400, detail="Only whisper supported")

    wav_path = None
    try:
        wav_path = normalize_to_whisper_wav(file_path)
        duration = get_audio_duration_sec(wav_path)

        diarize_enabled = (
            diarize
            if diarize is not None
            else bool(ALL_CONFIG.get("ASR", {}).get("DIARIZATION", False))
        )

        # ✅ Reuse singleton model
        asr = get_whisperx_client(ALL_CONFIG["ASR"]["MODEL_SIZE"])
        language = ALL_CONFIG["ASR"].get("LANGUAGE")

        t_start = time.time()

        # ✅ Load audio ONCE (float array @16k mono, WhisperX loader)
        t0 = time.time()
        audio = whisperx.load_audio(wav_path)
        load_audio_sec = round(time.time() - t0, 3)

        # ✅ Diarize ONCE on full audio (mandatory if diarize_enabled=True)
        diar_sec = 0.0
        diarization = None
        if diarize_enabled:
            t1 = time.time()
            diarization = asr.diarize_audio_array(
                audio,
                min_speakers=min_speakers,
                max_speakers=max_speakers,
            )
            diar_sec = round(time.time() - t1, 3)

        # ✅ Chunk IN MEMORY (no ffmpeg temp wav)
        chunk_sec = int(os.getenv("AUDIO_CHUNK_SEC", "60"))          # default 60 for speed
        overlap_sec = int(os.getenv("AUDIO_CHUNK_OVERLAP_SEC", "2")) # keep small
        chunks = chunk_audio_array(audio, chunk_sec, overlap_sec, sample_rate=16000)

        all_segments = []
        asr_sec_sum = 0.0

        # ✅ Transcribe chunks WITHOUT diarization
        for chunk_audio, offset in chunks:
            t2 = time.time()
            result = asr.transcribe_audio_array(chunk_audio, language=language)
            asr_sec_sum += (time.time() - t2)

            for seg in result.get("segments", []):
                seg["start"] = float(seg.get("start", 0.0)) + offset
                seg["end"] = float(seg.get("end", 0.0)) + offset
                all_segments.append(seg)

        # ✅ Assign speakers using global diarization timeline
        if diarize_enabled and diarization is not None:
            all_segments = asr.assign_speakers_to_segments(all_segments, diarization)
        else:
            for seg in all_segments:
                seg["speaker"] = seg.get("speaker", "Speaker 1")

        total_time = round(time.time() - t_start, 2)

        # Post-process + merge (same behavior)
        sentences = []
        for seg in all_segments:
            text = (seg.get("text") or "").strip()
            if not text:
                continue

            text = post_process_itn_output(
                text,
                ALL_CONFIG["ASR"].get("TEXT_NORMALIZATION", False),
            )

            speaker = seg.get("speaker", "Speaker 1")

            sentences.append({
                "speaker": speaker,
                "sentence": text,
                "start_time": round(seg["start"], 2),
                "end_time": round(seg["end"], 2),
            })

        out = {"transcript": merger.merge_sentences(sentences)}

        if debug_enabled:
            out["debug"] = {
                "no_of_calls": len(chunks),  # number of ASR chunk calls
                "audio_duration_sec": round(duration, 2),
                "diarization_enabled": diarize_enabled,
                "load_audio_sec": load_audio_sec,
                "diar_sec": diar_sec,
                "asr_sec_sum": round(asr_sec_sum, 2),
                "total_time_asr": total_time,
                "chunk_sec": chunk_sec,
                "overlap_sec": overlap_sec,
                "batch_size": int(os.getenv("WHISPERX_BATCH_SIZE", "32")),
            }

        return out

    finally:
        safe_remove(wav_path)
