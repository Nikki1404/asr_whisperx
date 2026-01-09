curl -w "\nTOTAL_TIME_SEC: %{time_total}\n" \
  -X POST "http://127.0.0.1:8003/asr/upload_folder" \
  -H "min-speakers: 1" \
  -H "max-speakers: 4" \
  -F "file=@test1.wav"
