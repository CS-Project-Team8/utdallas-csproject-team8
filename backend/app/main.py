from fastapi import FastAPI
from app.routers.dashboard import router as dashboard_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="YouTube Intelligence Platform API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(dashboard_router)

@app.get("/health")
def health():
    return {"status": "ok", "version": "v2"}


@app.on_event("startup")
def show_routes():
    print("\n=== REGISTERED ROUTES ===")
    for route in app.routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)
        print(methods, path)
    print("=========================\n")