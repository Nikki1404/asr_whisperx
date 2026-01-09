import whisperx
from app.config import settings

class WhisperXASR:
    def __init__(self):
        self.model = None

    def load(self):
        if self.model is None:
            self.model = whisperx.load_model(
                settings.model,
                device=settings.device,
                compute_type=settings.compute_type
            )

    def transcribe(self, audio_chunk):
        self.load()

        # WhisperX uses Faster-Whisper API
        # NO beam_size parameter allowed
        return self.model.transcribe(
            audio_chunk,
            batch_size=settings.batch_size,
            language=settings.language,
            vad_filter=settings.vad
        )
