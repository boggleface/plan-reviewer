import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

from .scheduler import schedule

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
DIST = ROOT / "frontend" / "dist"

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": jsonable_encoder(exc.errors()), "message": "Invalid request payload"},
    )


class TaskInput(BaseModel):
    id: str
    name: str
    owner: str | None = None
    duration_days: int
    depends_on: list[str] = []


class ScheduleRequest(BaseModel):
    tasks: list[TaskInput]
    deadline_day: int

    @field_validator("tasks")
    @classmethod
    def validate_tasks(cls, tasks: list[TaskInput]) -> list[TaskInput]:
        if len(tasks) > 60:
            raise ValueError("At most 60 tasks allowed")
        seen_ids = set()
        for t in tasks:
            if t.id in seen_ids:
                raise ValueError(f"Duplicate task id: {t.id}")
            seen_ids.add(t.id)
            if t.duration_days < 1:
                raise ValueError(f"duration_days must be at least 1: {t.id}")
        for t in tasks:
            for dep in t.depends_on:
                if dep not in seen_ids:
                    raise ValueError(f"Unknown dependency '{dep}' in task '{t.id}'")
        return tasks


@app.get("/api/plans")
def list_plans():
    plans = []
    plans_dir = DATA / "plans"
    if plans_dir.exists():
        for path in sorted(plans_dir.glob("*.md"), reverse=True):
            try:
                title = next(
                    (line.lstrip("# ").strip() for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("#")),
                    path.stem,
                )
            except Exception:
                title = path.stem
            plans.append({"id": path.stem, "title": title})
    return plans


@app.get("/api/plans/{plan_id}")
def get_plan(plan_id: str):
    plan_path = DATA / "plans" / f"{plan_id}.md"
    review_path = DATA / "reviews" / f"{plan_id}.json"
    if not plan_path.exists():
        raise HTTPException(status_code=404, detail=f"Plan not found: {plan_id}")
    if not review_path.exists():
        raise HTTPException(status_code=404, detail=f"Review not found: {plan_id}")

    text = plan_path.read_text(encoding="utf-8")
    review = json.loads(review_path.read_text(encoding="utf-8"))
    deadline = review.get("deadline_day")
    sched_deadline = deadline if deadline is not None else 0
    return {
        "id": plan_id,
        "text": text,
        "review": review,
        "schedule": schedule(review.get("tasks", []), sched_deadline),
    }


@app.post("/api/schedule")
def post_schedule(body: ScheduleRequest):
    tasks_dict = [t.model_dump() for t in body.tasks]
    return schedule(tasks_dict, body.deadline_day)


if DIST.exists():
    app.mount("/", StaticFiles(directory=DIST, html=True))
