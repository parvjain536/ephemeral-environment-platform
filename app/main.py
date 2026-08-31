from fastapi import FastAPI

app = FastAPI(
    title="Ephemeral Environment Platform",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "Ephemeral Environment Platform",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


@app.get("/version")
def version():
    return {
        "version": "0.1.0",
        "environment": "local",
    }