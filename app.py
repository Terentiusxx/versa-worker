import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import Response, StreamingResponse
from starlette.background import BackgroundTask

LLAMA_URL = os.environ.get("LLAMA_URL", "http://127.0.0.1:8080")

app = FastAPI()
client = httpx.AsyncClient(timeout=None)


@app.get("/ping")
async def ping():
    try:
        response = await client.get(f"{LLAMA_URL}/health", timeout=2.0)
        if response.status_code == 200:
            return Response(status_code=200)
        return Response(status_code=204)
    except Exception:
        return Response(status_code=204)


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def proxy(path: str, request: Request):
    target = f"{LLAMA_URL}/{path}"

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in {"host", "authorization", "content-length"}
    }

    body = await request.body()

    upstream_request = client.build_request(
        request.method,
        target,
        params=request.query_params,
        headers=headers,
        content=body,
    )

    upstream = await client.send(upstream_request, stream=True)

    response_headers = {
        key: value
        for key, value in upstream.headers.items()
        if key.lower() not in {
            "content-length",
            "transfer-encoding",
            "connection",
            "content-encoding",
        }
    }

    content_type = upstream.headers.get("content-type", "")

    if "text/event-stream" in content_type:
        return StreamingResponse(
            upstream.aiter_raw(),
            status_code=upstream.status_code,
            headers=response_headers,
            media_type="text/event-stream",
            background=BackgroundTask(upstream.aclose),
        )

    content = await upstream.aread()
    await upstream.aclose()

    return Response(
        content=content,
        status_code=upstream.status_code,
        headers=response_headers,
        media_type=content_type.split(";")[0] if content_type else None,
    )
