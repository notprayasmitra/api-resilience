from fastapi import FastAPI, Request, Response
import httpx

app = FastAPI(
    title="API Resilience & Failure Proxy",
    description="A proxy gateway to implement rate-limit monitoring and exponential backoff retries",
    version="1.0.0"
)

# We will be using HTTPBIN for testing our HTTP Requests
TARGET_API_URL = "https://httpbin.org"

@app.get("/health")
def health_check():
    return {"status": "healthy", "proxy_running": True}

# Master route to intercept all methods
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_gateway(path: str, request: Request):
    target_url = f"{TARGET_API_URL}/{path}"
    query_params = dict(request.query_params)
    body = await request.body()

    async with httpx.AsyncClient() as client:
        external_response = await client.request(
            method=request.method,
            url=target_url,
            params=query_params,
            content=body,
            headers=dict(request.headers), # Forward original headers
            timeout=10.0
        )

    return Response(
        content=external_response.content,
        status_code=external_response.status_code,
        headers=dict(external_response.headers)
    )