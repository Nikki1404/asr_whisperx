docker run --gpus all \
  -p 8003:8003 \
  -e DEVICE=cuda \
  -e COMPUTE_TYPE=float16 \
  -e WHISPER_MODEL=small \
  -e CHUNK_SEC=0.5 \
  -e STRIDE_SEC=0.15 \
  -e BATCH_SIZE=16 \
  -e BEAM_SIZE=1 \
  -e VAD=true \
  -e DIARIZE=true \
  -e HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxx \
  -e http_proxy=http://163.116.128.80:8080 \
  -e https_proxy=http://163.116.128.80:8080 \
  --name asr-whisperx \
  asr-whisperx
