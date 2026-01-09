from fastapi import FastAPI, UploadFile, File, Header, APIRouter
from pathlib import Path
import time

from utils.audio import to_wav_16k_mono
from utils.fileio import ensure_dir
from services.pipeline import OfflineASRPipeline
from services.exporters import save_json, save_txt

app = FastAPI()
router = APIRouter(prefix="/asr")

UPLOADS = "uploads"
OUTPUTS = "outputs"
ensure_dir(UPLOADS)
ensure_dir(OUTPUTS)

pipeline = OfflineASRPipeline()

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/upload_folder")
async def upload_folder(
    file: UploadFile = File(...),
    min_speakers: int | None = Header(None, convert_underscores=False),
    max_speakers: int | None = Header(None, convert_underscores=False),
):
    start = time.perf_counter()

    raw = Path(UPLOADS) / file.filename
    raw.write_bytes(await file.read())

    wav = to_wav_16k_mono(str(raw), UPLOADS)
    ttft, result = pipeline.run(wav, min_speakers, max_speakers)

    base = Path(file.filename).stem
    save_json(result, f"{OUTPUTS}/{base}.json")

    lines = [
        f"{seg.get('speaker','SPEAKER_00')}: {seg['text']}"
        for seg in result["segments"]
    ]
    save_txt(lines, f"{OUTPUTS}/{base}.txt")

    return {
        "file": file.filename,
        "ttft_ms": round(ttft * 1000, 2),
        "elapsed_sec": round(time.perf_counter() - start, 2),
        "segments": len(result["segments"])
    }

app.include_router(router)
