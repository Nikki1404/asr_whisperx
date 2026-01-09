from pydantic import BaseModel
import os

class Settings(BaseModel):
    device: str = os.getenv("DEVICE", "cuda")
    compute_type: str = os.getenv("COMPUTE_TYPE", "float16")
    model: str = os.getenv("WHISPER_MODEL", "small")
    language: str | None = os.getenv("LANGUAGE", None)

    chunk_sec: float = float(os.getenv("CHUNK_SEC", "0.5"))
    stride_sec: float = float(os.getenv("STRIDE_SEC", "0.15"))

    batch_size: int = int(os.getenv("BATCH_SIZE", "16"))
    beam_size: int = int(os.getenv("BEAM_SIZE", "1"))
    vad: bool = os.getenv("VAD", "true").lower() == "true"

    diarize: bool = os.getenv("DIARIZE", "true").lower() == "true"
    hf_token: str | None = os.getenv("HF_TOKEN", None)

    align: bool = False

settings = Settings()
