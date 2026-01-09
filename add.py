(base) root@EC03-E01-AICOE1:/home/CORP/re_nikitav/asr_whisperx/inspira_audio# curl -v http://127.0.0.1:8003/asr/health
* Uses proxy env variable http_proxy == 'http://163.116.128.80:8080'
*   Trying 163.116.128.80:8080...
* TCP_NODELAY set
* Connected to 163.116.128.80 (163.116.128.80) port 8080 (#0)
> GET http://127.0.0.1:8003/asr/health HTTP/1.1
> Host: 127.0.0.1:8003
> User-Agent: curl/7.68.0
> Accept: */*
> Proxy-Connection: Keep-Alive
>
* Mark bundle as not supporting multiuse
< HTTP/1.1 400 Bad Request
< Content-Length: 0
< Connection: close
<
* Closing connection 0
