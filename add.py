INFO:     Uvicorn running on http://0.0.0.0:8003 (Press CTRL+C to quit)
No language specified, language will be first be detected for each audio file (increases inference time).
>>Performing voice activity detection using Pyannote...
/usr/local/lib/python3.10/dist-packages/lightning_fabric/utilities/cloud_io.py:73: You are using `torch.load` with `weights_only=False` (the current default value), which uses the default pickle module implicitly. It is possible to construct malicious pickle data which will execute arbitrary code during unpickling (See https://github.com/pytorch/pytorch/blob/main/SECURITY.md#untrusted-models for more details). In a future release, the default value for `weights_only` will be flipped to `True`. This limits the functions that could be executed during unpickling. Arbitrary objects will no longer be allowed to be loaded via this mode unless they are explicitly allowlisted by the user via `torch.serialization.add_safe_globals`. We recommend you start setting `weights_only=True` for any use case where you don't have full control of the loaded file. Please open an issue on GitHub for any issues related to this experimental feature.
Lightning automatically upgraded your loaded checkpoint from v1.5.4 to v2.6.0. To apply the upgrade to your files permanently, run `python -m pytorch_lightning.utilities.upgrade_checkpoint ../usr/local/lib/python3.10/dist-packages/whisperx/assets/pytorch_model.bin`
Model was trained with pyannote.audio 0.0.1, yours is 3.4.0. Bad things might happen unless you revert pyannote.audio to 0.x.
Model was trained with torch 1.10.0+cu102, yours is 2.5.1+cu124. Bad things might happen unless you revert torch to 1.x.
INFO:     172.17.0.1:47818 - "POST /asr/upload_folder HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "/usr/local/lib/python3.10/dist-packages/uvicorn/protocols/http/h11_impl.py", line 410, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
  File "/usr/local/lib/python3.10/dist-packages/uvicorn/middleware/proxy_headers.py", line 60, in __call__
    return await self.app(scope, receive, send)
  File "/usr/local/lib/python3.10/dist-packages/fastapi/applications.py", line 1135, in __call__
    await super().__call__(scope, receive, send)
  File "/usr/local/lib/python3.10/dist-packages/starlette/applications.py", line 107, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/usr/local/lib/python3.10/dist-packages/starlette/middleware/errors.py", line 186, in __call__
    raise exc
  File "/usr/local/lib/python3.10/dist-packages/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, _send)
  File "/usr/local/lib/python3.10/dist-packages/starlette/middleware/exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/usr/local/lib/python3.10/dist-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/usr/local/lib/python3.10/dist-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/usr/local/lib/python3.10/dist-packages/fastapi/middleware/asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "/usr/local/lib/python3.10/dist-packages/starlette/routing.py", line 716, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/usr/local/lib/python3.10/dist-packages/starlette/routing.py", line 736, in app
    await route.handle(scope, receive, send)
  File "/usr/local/lib/python3.10/dist-packages/starlette/routing.py", line 290, in handle
    await self.app(scope, receive, send)
  File "/usr/local/lib/python3.10/dist-packages/fastapi/routing.py", line 115, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/usr/local/lib/python3.10/dist-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/usr/local/lib/python3.10/dist-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/usr/local/lib/python3.10/dist-packages/fastapi/routing.py", line 101, in app
    response = await f(request)
  File "/usr/local/lib/python3.10/dist-packages/fastapi/routing.py", line 355, in app
    raw_response = await run_endpoint_function(
  File "/usr/local/lib/python3.10/dist-packages/fastapi/routing.py", line 243, in run_endpoint_function
    return await dependant.call(**values)
  File "/app/app/main.py", line 36, in upload_folder
    result, timings = pipeline.run(wav, min_speakers, max_speakers)
  File "/app/services/pipeline.py", line 26, in run
    res = self.asr.transcribe(chunk)
  File "/app/services/whisperx_asr.py", line 18, in transcribe
    return self.model.transcribe(
TypeError: FasterWhisperPipeline.transcribe() got an unexpected keyword argument 'beam_size'
