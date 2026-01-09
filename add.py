import os
import time
import csv
import io
import boto3
import requests
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from botocore.config import Config


S3_BUCKET = "cx-speech"
S3_PREFIX = "asr-offline/load_testing_data/mp4_10_min/"

ASR_URL = "http://127.0.0.1:8002/asr/upload_file"
TIMEOUT = 1800  # seconds

# SAFE WORKER SETTINGS (GPU FRIENDLY)
WORKERS_MATRIX = [2, 3]          # DO NOT exceed GPU capacity
CHUNK_MATRIX = [60]              # diarization-friendly

WHISPERX_BATCH_SIZE = 48
FAST_DIARIZATION = 1

OUTPUT_CSV = f"whisperx_benchmark_final_{int(time.time())}.csv"

TMP_DIR = "/tmp/whisperx_s3"
os.makedirs(TMP_DIR, exist_ok=True)


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


def download_s3_file(key):
    local_path = os.path.join(TMP_DIR, os.path.basename(key))
    if not os.path.exists(local_path):
        s3.download_file(S3_BUCKET, key, local_path)
    return local_path


def get_audio_metadata(path):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=channels",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path,
    ]

    out = subprocess.check_output(cmd).decode().strip().split("\n")

    try:
        channels = int(out[0])
        duration = float(out[-1])
    except Exception:
        channels, duration = "", ""

    return channels, round(duration, 2) if duration else ""


def transcribe_local_file(entry, chunk_size):
    path = entry["path"]
    key = entry["key"]
    file_ext = path.split(".")[-1]

    os.environ["AUDIO_CHUNK_SEC"] = str(chunk_size)
    os.environ["WHISPERX_BATCH_SIZE"] = str(WHISPERX_BATCH_SIZE)
    os.environ["FAST_DIARIZATION"] = str(FAST_DIARIZATION)

    channels, audio_len = get_audio_metadata(path)

    gpu_util_before, gpu_mem_before = get_gpu_stats()
    start = time.time()

    with open(path, "rb") as f:
        files = {
            "file": (os.path.basename(path), f)
        }

        headers = {
            "diarization": "true",
            "debug": "no",
        }

        response = requests.post(
            ASR_URL,
            files=files,
            headers=headers,
            timeout=TIMEOUT,
        )

    latency = round(time.time() - start, 2)
    gpu_util_after, gpu_mem_after = get_gpu_stats()

    result = response.json()

    return {
        "file_name": os.path.basename(key),
        "file_format": file_ext,
        "channels": channels,
        "audio_len": audio_len,
        "latency": latency,
        "rtf": round(latency / audio_len, 2) if audio_len else "",
        "transcript": result.get("response", ""),
        "gpu_util_before": gpu_util_before,
        "gpu_mem_before": gpu_mem_before,
        "gpu_util_after": gpu_util_after,
        "gpu_mem_after": gpu_mem_after,
    }


def main():
    s3_files = list_s3_audio_files()
    print(f"\n Found {len(s3_files)} files in S3")

    print("  Pre-downloading files from S3...")
    entries = []
    for key in tqdm(s3_files):
        entries.append({
            "key": key,
            "path": download_s3_file(key)
        })

    rows = []

    for chunk_size in CHUNK_MATRIX:
        for workers in WORKERS_MATRIX:
            print(f"\n Running: workers={workers}, chunk={chunk_size}s")
            batch_start = time.time()

            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(transcribe_local_file, e, chunk_size): e
                    for e in entries
                }

                for future in tqdm(as_completed(futures), total=len(futures)):
                    r = future.result()
                    channel_type = (
                        "mono" if r["channels"] == 1
                        else "stereo" if r["channels"] == 2
                        else ""
                    )

                    rows.append([
                        r["file_name"],
                        workers,
                        chunk_size,
                        r["file_format"],
                        channel_type,
                        r["audio_len"],
                        r["latency"],
                        r["rtf"],
                        "whisperx",
                        FAST_DIARIZATION,
                        WHISPERX_BATCH_SIZE,
                        r["gpu_util_before"],
                        r["gpu_mem_before"],
                        r["gpu_util_after"],
                        r["gpu_mem_after"],
                        r["transcript"],
                    ])

            print(f"⏱ Batch time: {round(time.time() - batch_start, 2)} sec")


    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "file_name",
            "num_workers",
            "chunk_size_sec",
            "file_format",
            "channels",
            "audio_length_sec",
            "single_file_latency_sec",
            "rtf",
            "model",
            "fast_diarization",
            "batch_size",
            "gpu_util_before_pct",
            "gpu_mem_before_mb",
            "gpu_util_after_pct",
            "gpu_mem_after_mb",
            "transcript",
        ])
        writer.writerows(rows)

    print("\n BENCHMARK COMPLETE")
    print(f" CSV saved to: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
