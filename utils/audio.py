from pathlib import Path
import ffmpeg

def to_wav_16k_mono(input_path: str, out_dir: str) -> str:
    out = Path(out_dir) / (Path(input_path).stem + "_16k.wav")
    out.parent.mkdir(parents=True, exist_ok=True)

    (
        ffmpeg
        .input(input_path)
        .output(str(out), ac=1, ar=16000, format="wav")
        .overwrite_output()
        .run(quiet=True)
    )
    return str(out)
