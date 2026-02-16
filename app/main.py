from fastapi import FastAPI

app = FastAPI(
    title="FastAPI Gitops Pipeline",
    description="A simple FastAPI application to demonstrate GitOps pipeline",
    version="1.0.0",
)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI GitOps Pipeline!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}