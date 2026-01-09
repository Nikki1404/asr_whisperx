curl -X POST "http://127.0.0.1:8002/asr/upload_file" \
  -H "debug: yes" \
  -H "diarization: true" \
  -H "min-speakers: 1" \
  -H "max-speakers: 4" \
  -F "file=@test1.wav"
