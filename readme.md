
## WhisperX Load Test (CX Calls)

 This setup benchmarks WhisperX on real CX call recordings pulled from S3 and shows the true GPU transcription speed.

  We found out something important:
  '''
  WhisperX was never slow — diarization was.
'''

#### What this does:

    -Downloads CX call audio from S3
    -Caches them in /tmp/whisperx_s3
    -Sends them to WhisperX FastAPI
    -Runs multiple files in parallel

##### Logs:
    -latency
    -RTF
    -GPU usage
    -transcript

Saves everything to a CSV
'''
S3 → /tmp/whisperx_s3 → WhisperX → CSV
'''

No re-downloads
No diarization
GPU fully used

### Whisper vs WhisperX – 

#### Whisper
    - Very fast for pure transcription
    - ~20–30 sec for 5-min audio on GPU
    - Speed is mostly GPU-bound
    - No speaker labels

#### WhisperX

    - Uses the same Whisper ASR → same speed for transcription
    - Adds diarization + alignment on top
    - With diarization OFF → same speed as Whisper
    - With diarization ON → 4–6× slower due to PyAnnote

##### Real latency we saw
'''
Mode	                    5-min call
WhisperX (no diarization)	~25 sec
WhisperX (with diarization)	~150 sec
'''

- Whisper itself finishes in ~15–25 sec.
- Diarization alone takes ~130 sec.

##### Sample output (fast mode – no diarization)
bash
'''
{
  "speaker": "Speaker 1",
  "sentence": "Thank you, thank you. Absolutely, you two. Is there anything else I may assist with before I let you go? No, that's it. Thank you. I really appreciate it. Bye.",
  "start_time": 5568.03,
  "end_time": 5592.57
}
'''

- response_time ≈ 25 sec

##### Sample with diarization (slow)
'''
with diarization output :
,{"speaker":"SPEAKER_00","sentence":"No, I will ask with them that as well. We are looking for financing, right? So we don't need you. So I am going to hang up the call as well, okay? Yes, please. All right. Thank you. Thank you for calling. Thank you, Lily. Hold the line. Yeah, please hold the line.","start_time":7999.09,"end_time":8021.78}],"response_time":150.36,"debug":{"no_of_calls":1,"total_time_asr":147.66,"audio_duration_sec":8021.76,"rtf":0.018,"diarization_enabled":true,"last_segment_end_sec":8021.78,"whisperx_perf":{"load_audio_sec":1.864,"asr_sec":14.094,"diar_sec":131.428,"assign_sec":0.255,"mode":"fast_no_align","batch_size":32,"device":"cuda","compute_type":"float16"}}}
'''

- Whisper ASR: ~14 sec  
- Diarization: ~131 sec  
- Total: ~150 sec



- That called PyAnnote many times per file → huge slowdown.

##### What this means for CX use

- If you only need text → run WhisperX without diarization


###### Start server
'''
docker build -t asr-whisperx .
'''
'''
docker run --gpus all \
  -p 8002:8002 \
  -e HF_TOKEN=hf_xxx \
  -e WHISPERX_BATCH_SIZE=48 \
  -e AUDIO_CHUNK_SEC=60 \
  asr-whisperx
'''

###### Test fast mode
'''
time curl -X POST http://127.0.0.1:8002/asr/upload_file \
  -H "diarization: false" \
  -F "file=@audio_5min.wav"
'''

Expected:
5 min → ~20–30 sec

###### Run S3 benchmark
'''
python whisperx_benchmark_fast.py
'''

##### Results :

- whisperx_fast_<timestamp>.csv

Bottom line

- Whisper is fast 
- WhisperX ASR is equally fast 
- Diarization is what adds cost 
