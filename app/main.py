import asyncio
from fastapi import FastAPI, Request, Response, HTTPException
import httpx

app = FastAPI(
    title="API Resilience & Failure Proxy",
    description="A proxy gateway to implement rate-limit monitoring and exponential backoff retries",
    version="1.0.0"
)

# We will be using HTTPBIN for testing our HTTP Requests
TARGET_API_URL = "https://httpbin.org"

# Resilience Settings
MAX_RETRIES = 3
INITIAL_BACKOFF_SECS = 1.0

@app.get("/health")
def health_check():
    return {"status": "healthy", "proxy_running": True}

# Master route to intercept all methods
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_gateway(path: str, request: Request):
    target_url = f"{TARGET_API_URL}/{path}"
    query_params = dict(request.query_params)
    body = await request.body()

    current_backoff = INITIAL_BACKOFF_SECS

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient() as client:
                external_response = await client.request(
                    method=request.method,
                    url=target_url,
                    params=query_params,
                    content=body,
                    headers=dict(request.headers), # forward original headers
                    timeout=5.0  # 5 second timeout limit per attempt
                )

            if external_response.status_code >= 500:
                raise httpx.HTTPStatusError(
                    f"Server Error {external_response.status_code}", 
                    request=None, 
                    response=external_response
                )
            
            return Response(
                content=external_response.content,
                status_code=external_response.status_code,
                headers=dict(external_response.headers)
            )
        
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            # if we used up all our attempts, show failure message
            if attempt == MAX_RETRIES:
                raise HTTPException(
                    status_code=502, 
                    detail=f"Target API unavailable after {MAX_RETRIES} attempts. Error: {str(exc)}"
                )
            
            print(f"[Attempt {attempt} Failed] Waiting {current_backoff}s before retry...")
            await asyncio.sleep(current_backoff)
            current_backoff *= 2