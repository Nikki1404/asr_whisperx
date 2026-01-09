@app.post("/upload_file")
async def upload_file(
    request: Request,
    file: UploadFile = File(...)
):
    path = f"/tmp/{uuid.uuid4()}_{file.filename}"

    # 🔑 Read headers
    diarize = request.headers.get("diarization", "true").lower() == "true"
    debug_enabled = request.headers.get("debug", "false").lower() == "yes"

    min_speakers = request.headers.get("min-speakers")
    max_speakers = request.headers.get("max-speakers")

    min_speakers = int(min_speakers) if min_speakers else None
    max_speakers = int(max_speakers) if max_speakers else None

    try:
        with open(path, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                f.write(chunk)

        st = time.time()

        result = process_audio_file(
            path,
            diarize=diarize,
            min_speakers=min_speakers,
            max_speakers=max_speakers,
            debug_enabled=debug_enabled
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
