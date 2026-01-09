# main.py
import os
import time
import uuid
import jiwer
import numpy as np
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from config import ALL_CONFIG
from components.logger import get_logger
from components.audio_processing import process_audio_file
from components.whisperx_asr import get_whisperx_client

logger = get_logger("main")


class WerData(BaseModel):
    ground_truth: str
    transcription: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Preloading WhisperX + diarizer at startup")

    wx = get_whisperx_client(ALL_CONFIG["ASR"]["MODEL_SIZE"])

    # Warm diarizer
    try:
        wx._ensure_diarizer()
        logger.info("Diarizer loaded")
    except Exception as e:
        logger.error(f"Diarizer load failed: {e}")
        # diarization is mandatory for you, so failing here is good to catch early

    # Warm ASR + diarizer with 1 sec dummy audio to reduce first-request latency
    try:
        dummy = np.zeros(16000, dtype=np.float32)
        _ = wx.transcribe_audio_array(dummy, language=ALL_CONFIG["ASR"].get("LANGUAGE"))
        _ = wx.diarize_audio_array(dummy)
        logger.info("Warmup done (ASR + diar)")
    except Exception as e:
        logger.warning(f"Warmup skipped: {e}")

    yield


app = FastAPI(
    title="ASR Offline Whisper",
    root_path="/asr",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=["*"],
)


@app.post("/upload_file")
async def upload_file(
    request: Request,
    file: UploadFile = File(...)
):
    path = f"/tmp/{uuid.uuid4()}_{file.filename}"

    try:
        with open(path, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                f.write(chunk)

        # diarization mandatory → keep True
        # optionally you can override via header diarization:true/false later
        diarize = True

        st = time.time()
        result = process_audio_file(path, diarize=diarize, debug_enabled=True)

        return {
            "status": 200,
            "response": result["transcript"],
            "response_time": round(time.time() - st, 2),
            "debug": result.get("debug"),
        }

    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        if os.path.exists(path):
            os.remove(path)


@app.post("/wer_score")
async def calculate_wer(data: WerData):
    return {"wer": jiwer.wer(data.ground_truth, data.transcription)}


if __name__ == "__main__":
    logger.info("Application is up (asr-offline-whisper)")
    uvicorn.run("main:app", host="0.0.0.0", port=8002)
