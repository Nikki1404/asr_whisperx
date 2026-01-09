docker run --gpus all \
  -p 8002:8002 \
  -e HF_TOKEN=hf_ \
  -e FAST_DIARIZATION=1 \
  -e WHISPERX_BATCH_SIZE=48 \
  -e AUDIO_CHUNK_SEC=60 \
  -e AUDIO_CHUNK_OVERLAP_SEC=2 \
  asr-whisperx
