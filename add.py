@app.post("/upload_file")
async def upload_file(
    request: Request,
    file: UploadFile = File(...)
):
    path = f"/tmp/{uuid.uuid4()}_{file.filename}"

    try:
        # Save uploaded file
        with open(path, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                f.write(chunk)

        diarize = request.headers.get("diarization")
        if diarize is not None:
            diarize = diarize.lower() == "true"
        else:
            diarize = bool(ALL_CONFIG.get("ASR", {}).get("DIARIZATION", False))

        # Speaker bounds (optional)
        min_speakers = request.headers.get("min-speakers")
        max_speakers = request.headers.get("max-speakers")

        min_speakers = int(min_speakers) if min_speakers else None
        max_speakers = int(max_speakers) if max_speakers else None

        debug_enabled = request.headers.get("debug", "false").lower() == "true"

        st = time.time()

        result = process_audio_file(
            path,
            diarize=diarize,
            min_speakers=min_speakers,
            max_speakers=max_speakers,
            debug_enabled=debug_enabled,
        )

        return {
            "status": 200,
            "response": result["transcript"],
            "response_time": round(time.time() - st, 2),
            "debug": result.get("debug"),
        }

    except Exception as e:
        raise HTTPException(500, str(e))

    finally:
        if os.path.exists(path):
            os.remove(path)
