from fastapi import FastAPI

app = FastAPI(title="YouTube Intelligence Platform API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok", "version":"v2"}