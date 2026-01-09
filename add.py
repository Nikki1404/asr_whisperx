# components/whisperx_asr.py
import os
import threading
import time
from typing import Optional, Dict, Any, List

import torch
import torch.serialization
import whisperx
from whisperx.diarize import DiarizationPipeline

from components.logger import get_logger

logger = get_logger("whisperx-asr")


def _overlap(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


class WhisperXDiarizationClient:
    """
    WhisperX wrapper:
      - Transcription
      - Diarization (pyannote)
      - Speaker assignment by overlap (FAST)

    IMPORTANT CHANGE:
      - We expose methods to:
          diarize once on full audio
          transcribe chunks without diarizing each chunk
          then assign speakers using overlap
    """

    _lock = threading.Lock()
    _instances = {}

    def __new__(cls, model_size: str = "base"):
        with cls._lock:
            if model_size not in cls._instances:
                inst = super().__new__(cls)
                inst._init(model_size)
                cls._instances[model_size] = inst
        return cls._instances[model_size]

    def _init(self, model_size: str):
        self.model_size = model_size
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.compute_type = "float16" if self.device == "cuda" else "int8"

        if self.device == "cuda":
            torch.backends.cudnn.benchmark = True
            try:
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
            except Exception:
                pass

        logger.info(
            f"Loading WhisperX model='{model_size}' device='{self.device}' compute='{self.compute_type}'"
        )

        self.model = whisperx.load_model(
            model_size,
            self.device,
            compute_type=self.compute_type,
        )

        self.diarize_model = None
        logger.info("WhisperX ASR model loaded")

    def _patch_torch_for_pyannote(self):
        try:
            from omegaconf.listconfig import ListConfig
            from omegaconf.dictconfig import DictConfig
            torch.serialization.add_safe_globals([ListConfig, DictConfig])
        except Exception:
            pass

    def _ensure_diarizer(self):
        if self.diarize_model is not None:
            return

        hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
        if not hf_token:
            raise RuntimeError("HF_TOKEN not set for diarization")

        self._patch_torch_for_pyannote()

        logger.info("Loading diarization pipeline (pyannote)")
        self.diarize_model = DiarizationPipeline(
            use_auth_token=hf_token,
            device=self.device,
        )


    def assign_speakers_to_segments(
        self,
        segments: List[Dict[str, Any]],
        diarization,
        default_speaker: str = "SPEAKER_00",
    ) -> List[Dict[str, Any]]:
        turns = []


        if hasattr(diarization, "iterrows"):  # pandas DataFrame
            for _, r in diarization.iterrows():
                turns.append((float(r["start"]), float(r["end"]), str(r["speaker"])))
        elif hasattr(diarization, "itertracks"):  # pyannote Annotation
            for seg, _, label in diarization.itertracks(yield_label=True):
                turns.append((float(seg.start), float(seg.end), str(label)))

        for s in segments:
            s0, s1 = float(s["start"]), float(s["end"])
            best_spk, best_ov = default_speaker, 0.0
            for t0, t1, spk in turns:
                ov = _overlap(s0, s1, t0, t1)
                if ov > best_ov:
                    best_ov, best_spk = ov, spk
            s["speaker"] = best_spk

        return segments


    def diarize_audio_array(
        self,
        audio,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None,
    ):
        """
        Run diarization ONCE for the full audio.
        """
        self._ensure_diarizer()

        # depending on pyannote version, min/max speakers may or may not work.
        # We'll pass only if provided.
        kwargs = {}
        if min_speakers is not None:
            kwargs["min_speakers"] = min_speakers
        if max_speakers is not None:
            kwargs["max_speakers"] = max_speakers

        return self.diarize_model(audio, **kwargs)

    def transcribe_audio_array(
        self,
        audio,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transcribe an audio array (chunk) WITHOUT diarization.
        """
        batch_size = int(os.getenv("WHISPERX_BATCH_SIZE", "32"))

        t1 = time.perf_counter()
        result = self.model.transcribe(audio, language=language, batch_size=batch_size)
        asr_sec = round(time.perf_counter() - t1, 3)

        # attach perf
        result["__perf"] = {
            "asr_sec": asr_sec,
            "batch_size": batch_size,
            "device": self.device,
            "compute_type": self.compute_type,
        }
        return result


# =====================================================
# GLOBAL SINGLETON ACCESSOR
# =====================================================
_GLOBAL_WX_CLIENT = None
_GLOBAL_WX_LOCK = threading.Lock()


def get_whisperx_client(model_size: str = "base") -> WhisperXDiarizationClient:
    global _GLOBAL_WX_CLIENT
    with _GLOBAL_WX_LOCK:
        if _GLOBAL_WX_CLIENT is None:
            logger.info("Creating global WhisperXDiarizationClient (singleton)")
            _GLOBAL_WX_CLIENT = WhisperXDiarizationClient(model_size)
    return _GLOBAL_WX_CLIENT
