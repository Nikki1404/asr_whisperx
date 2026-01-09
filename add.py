from fastapi import FastAPI, UploadFile, File, Header, APIRouter
from pathlib import Path
import time

from utils.audio import to_wav_16k_mono
from utils.fileio import ensure_dir
from services.pipeline import OfflineASRPipeline

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

    result, timings = pipeline.run(wav, min_speakers, max_speakers)

    e2e_ms = round((time.perf_counter() - start) * 1000, 2)

    return {
        "file": file.filename,

        # ✅ LATENCY
        "latency_ms": {
            "asr_latency_ms": timings["asr_ttft_ms"],
            "processing_latency_ms": timings["asr_total_ms"],
            "e2e_latency_ms": e2e_ms
        },

        # 🔍 DETAILED TIMINGS
        "timings_ms": timings,

        "segments": len(result["segments"])
    }

app.include_router(router)

121.2 Successfully built antlr4-python3-runtime docopt julius
121.2 ERROR: Exception:
121.2 Traceback (most recent call last):
121.2   File "/usr/lib/python3/dist-packages/pip/_internal/cli/base_command.py", line 165, in exc_logging_wrapper
121.2     status = run_func(*args)
121.2   File "/usr/lib/python3/dist-packages/pip/_internal/cli/req_command.py", line 205, in wrapper
121.2     return func(self, options, args)
121.2   File "/usr/lib/python3/dist-packages/pip/_internal/commands/install.py", line 389, in run
121.2     to_install = resolver.get_installation_order(requirement_set)
121.2   File "/usr/lib/python3/dist-packages/pip/_internal/resolution/resolvelib/resolver.py", line 188, in get_installation_order
121.2     weights = get_topological_weights(
121.2   File "/usr/lib/python3/dist-packages/pip/_internal/resolution/resolvelib/resolver.py", line 276, in get_topological_weights
121.2     assert len(weights) == expected_node_count
121.2 AssertionError
------
Dockerfile:24
--------------------
  22 |
  23 |     COPY requirements.txt .
  24 | >>> RUN pip3 install --no-cache-dir -r requirements.txt
  25 |
  26 |     COPY . .
--------------------
ERROR: failed to build: failed to solve: process "/bin/sh -c pip3 install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 2
(base) root@EC03-E01-AICOE1:/home/CORP/re_nikitav/asr_whisperx#
