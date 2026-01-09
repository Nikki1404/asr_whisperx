import whisperx
from app.config import settings
from services.whisperx_asr import WhisperXASR
from services.diarize import Diarizer
from services.chunker import iter_chunks
from utils.timers import stopwatch

class OfflineASRPipeline:
    def __init__(self):
        self.asr = WhisperXASR()
        self.diar = Diarizer()

    def run(self, wav_path, min_speakers=None, max_speakers=None):
        timings = {}

        audio = whisperx.load_audio(wav_path)
        sr = 16000
        segments = []

        # ---------------- ASR ----------------
        ttft_ms = None
        with stopwatch() as asr_timer:
            for chunk, offset in iter_chunks(
                audio, sr, settings.chunk_sec, settings.stride_sec
            ):
                res = self.asr.transcribe(chunk)
                for s in res.get("segments", []):
                    s["start"] += offset
                    s["end"] += offset
                    segments.append(s)

                if ttft_ms is None and segments:
                    ttft_ms = asr_timer()

        timings["asr_ttft_ms"] = round(ttft_ms, 2)
        timings["asr_total_ms"] = round(asr_timer(), 2)

        # ---------------- DIARIZATION ----------------
        if settings.diarize:
            with stopwatch() as diar_timer:
                diar = self.diar.run(wav_path, min_speakers, max_speakers)
            timings["diarization_ms"] = round(diar_timer(), 2)

            with stopwatch() as merge_timer:
                result = whisperx.assign_word_speakers(
                    diar, {"segments": segments}
                )
            timings["merge_ms"] = round(merge_timer(), 2)
        else:
            result = {"segments": segments}
            timings["diarization_ms"] = 0.0
            timings["merge_ms"] = 0.0

        return result, timings

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
