from fastapi import FastAPI, HTTPException
import os

app = FastAPI(
    title="FastAPI Gitops Pipeline",
    description="A simple FastAPI application to demonstrate GitOps pipeline",
    version="1.0.0",
)

ENVIRONMENT = os.environ.get("ENVIRONMENT", "unknown")
VERSION = os.environ.get("VERSION", "1.0.0")
FAIL_HEALTH = os.environ.get("FAIL_HEALTH", "false").lower() == "true"

@app.get("/")
async def read_root():
    return {
        "message": "Welcome to the FastAPI GitOps Pipeline Demo!",
        "environment": ENVIRONMENT,
        "version": "1.0.0"
        }

@app.get("/health")
async def health_check():
    if FAIL_HEALTH:
        raise HTTPException(status_code=503, detail="Service unhealthy")
    return {"status": "healthy", "version": VERSION}
    return {"status": "healthy"}

@app.get("/version")
def get_version():
    return {"version": VERSION}
