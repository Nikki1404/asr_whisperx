from pathlib import Path
import subprocess

def to_wav_16k_mono(input_path: str, out_dir: str) -> str:
    input_path = Path(input_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{input_path.stem}_16k.wav"

    if input_path.suffix.lower() == ".wav":
        try:
            probe = subprocess.check_output(
                [
                    "ffprobe", "-v", "error",
                    "-select_streams", "a:0",
                    "-show_entries", "stream=channels,sample_rate",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(input_path)
                ],
                text=True
            ).strip().split("\n")

            if int(probe[0]) == 1 and int(probe[1]) == 16000:
                return str(input_path)
        except Exception:
            pass

    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(input_path),
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            "-c:a", "pcm_s16le",
            "-threads", "0",
            str(out_path)
        ],
        check=True
    )
    return str(out_path)

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
