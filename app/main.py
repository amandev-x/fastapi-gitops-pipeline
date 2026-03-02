from fastapi import FastAPI
import os

app = FastAPI(
    title="FastAPI Gitops Pipeline",
    description="A simple FastAPI application to demonstrate GitOps pipeline",
    version="1.0.0",
)

ENVIRONMENT = os.environ.get("ENVIRONMENT", "unknown")
@app.get("/")
async def read_root():
    return {
        "message": "Welcome to the FastAPI GitOps Pipeline Demo!",
        "environment": ENVIRONMENT,
        "version": "1.0.0"
        }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}