from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
import httpx
import json
import os

app = FastAPI()

NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

@app.post("/v1/chat/completions")
async def proxy_chat_completions(request: Request):
    # 1. Ambil body dan API Key
    body = await request.json()
    auth_header = request.headers.get("Authorization")
    
    # Ambil API Key dari env var jika tidak dikirim oleh client
    api_key = auth_header if auth_header else f"Bearer {os.getenv('NVIDIA_API_KEY')}"

    # 2. Pastikan extra_body untuk thinking selalu aktif
    if "extra_body" not in body:
        body["extra_body"] = {}
    
    if "chat_template_kwargs" not in body["extra_body"]:
        body["extra_body"]["chat_template_kwargs"] = {"thinking": True}
    else:
        body["extra_body"]["chat_template_kwargs"]["thinking"] = True

    # 3. Fungsi generator untuk streaming
    async def stream_generator():
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                NVIDIA_API_URL,
                headers={
                    "Authorization": api_key,
                    "Content-Type": "application/json",
                },
                json=body,
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        # Kirim kembali setiap baris data (SSE format)
                        yield f"{line}\n\n"

    # 4. Return sebagai StreamingResponse
    return StreamingResponse(stream_generator(), media_type="text/event-stream")

# Agar Vercel bisa mengenali app
@app.get("/")
def read_root():
    return {"status": "Proxy is running"}
    