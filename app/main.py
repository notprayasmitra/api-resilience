from fastapi import FastAPI

app = FastAPI(
    title="API Resilience",
    description="A proxy gateway to implement rate-limit monitoring",
    version="1.0.0"
)

@app.get("/health")

def health_check():
    return{"status": "healthy", "proxy_running": True}