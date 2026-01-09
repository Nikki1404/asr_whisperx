@app.post("/upload_file")
async def upload_file(
    request: Request,
    file: UploadFile = File(...)
):
    path = f"/tmp/{uuid.uuid4()}_{file.filename}"

    try:
        with open(path, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                f.write(chunk)

        # diarization mandatory → keep True
        # optionally you can override via header diarization:true/false later
        diarize = True

        st = time.time()
        result = process_audio_file(path, diarize=diarize, debug_enabled=True)

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
