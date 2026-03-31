from fastapi import FastAPI
from app.routers.dashboard import router as dashboard_router
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth import router as auth_router
from app.routers.invite import router as invites_router
from app.routers.movies import router as movies_router


app = FastAPI(title="YouTube Intelligence Platform API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "https://utdallas-csproject-team8-msggmucge-aashish-kambalas-projects.vercel.app/"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)
app.include_router(auth_router)
app.include_router(invites_router)
app.include_router(movies_router)


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