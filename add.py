import os
import time
import csv
import boto3
import requests
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from botocore.config import Config

S3_BUCKET = "cx-speech"
S3_PREFIX = "asr-offline/load_testing_data/mp4_10_min/"
ASR_URL = "http://127.0.0.1:8002/asr/upload_file"
TIMEOUT = 1800

TMP_DIR = "/tmp/whisperx_s3"
os.makedirs(TMP_DIR, exist_ok=True)

WORKERS = 3                 # GPU safe parallelism
AUDIO_CHUNK_SEC = 60
WHISPERX_BATCH_SIZE = 48

OUTPUT_CSV = f"whisperx_fast_{int(time.time())}.csv"


s3 = boto3.client(
    "s3",
    config=Config(
        max_pool_connections=50,
        retries={"max_attempts": 3},
    ),
)

def get_gpu_stats():
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used",
                "--format=csv,noheader,nounits",
            ]
        ).decode().strip()
        util, mem = out.split(",")
        return int(util), int(mem)
    except Exception:
        return "", ""

def list_s3_audio_files():
    paginator = s3.get_paginator("list_objects_v2")
    keys = []
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=S3_PREFIX):
        for obj in page.get("Contents", []):
            if obj["Key"].lower().endswith((".wav", ".mp4")):
                keys.append(obj["Key"])
    return keys

def download_s3(key):
    path = os.path.join(TMP_DIR, os.path.basename(key))
    if not os.path.exists(path):
        s3.download_file(S3_BUCKET, key, path)
    return path

def get_audio_metadata(path):
    try:
        out = subprocess.check_output(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "a:0",
                "-show_entries", "stream=channels",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                path,
            ]
        ).decode().strip().split("\n")

        return int(out[0]), round(float(out[-1]), 2)
    except Exception:
        return "", ""

def transcribe(path):
    os.environ["AUDIO_CHUNK_SEC"] = str(AUDIO_CHUNK_SEC)
    os.environ["WHISPERX_BATCH_SIZE"] = str(WHISPERX_BATCH_SIZE)

    channels, audio_len = get_audio_metadata(path)
    gpu_before = get_gpu_stats()

    start = time.time()

    with open(path, "rb") as f:
        r = requests.post(
            ASR_URL,
            files={"file": (os.path.basename(path), f)},
            headers={"diarization": "false"},
            timeout=TIMEOUT,
        )

    latency = round(time.time() - start, 2)
    gpu_after = get_gpu_stats()

    return {
        "file": os.path.basename(path),
        "channels": channels,
        "audio_len": audio_len,
        "latency": latency,
        "rtf": round(latency / audio_len, 2) if audio_len else "",
        "gpu_before": gpu_before,
        "gpu_after": gpu_after,
        "text": r.json().get("response", ""),
    }

def main():
    keys = list_s3_audio_files()
    print(f"\n Found {len(keys)} files in S3")

    print(" Downloading from S3 once...")
    paths = [download_s3(k) for k in tqdm(keys)]

    rows = []

    print("\n Running fast WhisperX (no diarization)")
    start = time.time()

    with ThreadPoolExecutor(max_workers=WORKERS) as exe:
        futures = [exe.submit(transcribe, p) for p in paths]

        for f in tqdm(as_completed(futures), total=len(futures)):
            r = f.result()
            rows.append([
                r["file"],
                r["channels"],
                r["audio_len"],
                r["latency"],
                r["rtf"],
                WHISPERX_BATCH_SIZE,
                r["gpu_before"][0],
                r["gpu_before"][1],
                r["gpu_after"][0],
                r["gpu_after"][1],
                r["text"],
            ])

    print(f"\n Total wall time: {round(time.time()-start,2)} sec")

    # Write CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "file",
            "channels",
            "audio_length_sec",
            "latency_sec",
            "rtf",
            "batch_size",
            "gpu_util_before",
            "gpu_mem_before",
            "gpu_util_after",
            "gpu_mem_after",
            "transcript",
        ])
        writer.writerows(rows)

    print(f"\n Saved → {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
