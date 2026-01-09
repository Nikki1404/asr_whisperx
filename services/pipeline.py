import whisperx
from app.config import settings
from services.whisperx_asr import WhisperXASR
from services.diarize import Diarizer
from services.chunker import iter_chunks
from utils.timers import timer

class OfflineASRPipeline:
    def __init__(self):
        self.asr = WhisperXASR()
        self.diar = Diarizer()

    def run(self, wav_path, min_speakers=None, max_speakers=None):
        audio = whisperx.load_audio(wav_path)
        sr = 16000

        segments = []
        ttft = None

        with timer() as total:
            for chunk, offset in iter_chunks(
                audio, sr,
                settings.chunk_sec,
                settings.stride_sec
            ):
                result = self.asr.transcribe(chunk)
                for s in result.get("segments", []):
                    s["start"] += offset
                    s["end"] += offset
                    segments.append(s)

                if ttft is None and segments:
                    ttft = total()

        result = {"segments": segments}

        if settings.diarize:
            diar = self.diar.run(wav_path, min_speakers, max_speakers)
            result = whisperx.assign_word_speakers(diar, result)

        return ttft or total(), result
