import threading
from app.youtubeapi_pipelinetest import run_pipeline_for_studio
from app.app import run_llm_for_studio
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.db_routes import get_conn
from app.db_operationstest import insert_movie_rating

router = APIRouter()

# In-memory status tracker per studio
pipeline_status: dict[str, str] = {}


def get_studio_name(studio_id: str) -> str | None:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM studios WHERE studioid = %s", (studio_id,))
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()


@router.post("/api/v1/studios/{studio_id}/run-pipeline")
def trigger_pipeline(studio_id: str):
    if pipeline_status.get(studio_id) == "running":
        return JSONResponse(status_code=409, content={"status": "already_running"})

    studio_name = get_studio_name(studio_id)
    if not studio_name:
        return JSONResponse(status_code=404, content={"error": "Studio not found"})

    def run():
        pipeline_status[studio_id] = "running"
        try:
            # Step 1: collect data
            run_pipeline_for_studio(studio_id)
            # Step 2: run LLM analysis on all movies
            run_llm_for_studio(studio_id)
        except Exception as e:
            print(f"Pipeline error for {studio_id}: {e}")
        finally:
            pipeline_status[studio_id] = "idle"
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return JSONResponse(status_code=202, content={"status": "started"})


@router.get("/api/v1/studios/{studio_id}/pipeline-status")
def get_pipeline_status(studio_id: str):
    status = pipeline_status.get(studio_id, "idle")
    return {"status": status}