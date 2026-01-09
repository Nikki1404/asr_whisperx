import whisperx
from app.config import settings

class Diarizer:
    def __init__(self):
        self.pipeline = None

    def load(self):
        if self.pipeline is None:
            self.pipeline = whisperx.DiarizationPipeline(
                use_auth_token=settings.hf_token,
                device=settings.device
            )

    def run(self, wav_path: str, min_speakers=None, max_speakers=None):
        self.load()
        return self.pipeline(
            wav_path,
            min_speakers=min_speakers,
            max_speakers=max_speakers
        )
