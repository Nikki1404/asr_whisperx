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
