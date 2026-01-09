import whisperx
from app.config import settings

class WhisperXASR:
    def __init__(self):
        self.model = None

    def load(self):
        if self.model is None:
            # VAD is enabled here for Faster-Whisper
            self.model = whisperx.load_model(
                settings.model,
                device=settings.device,
                compute_type=settings.compute_type,
                vad=settings.vad
            )

    def transcribe(self, audio_chunk):
        self.load()

        # Faster-Whisper API (WhisperX 3.x)
        # NO beam_size, NO vad_filter
        return self.model.transcribe(
            audio_chunk,
            batch_size=settings.batch_size,
            language=settings.language
        )
