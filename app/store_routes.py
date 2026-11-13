from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app import db
from app.models import ReconciliationReport

router = APIRouter(prefix="/runs", tags=["runs"])


class RunSummary(BaseModel):
    id: int
    created_at: str


@router.get("", response_model=list[RunSummary])
def list_runs(limit: int = Query(20, ge=1, le=100)) -> list[RunSummary]:
    return [RunSummary(id=r["id"], created_at=r["created_at"]) for r in db.list_runs(limit)]


@router.get("/{run_id}", response_model=ReconciliationReport)
def get_run(run_id: int) -> ReconciliationReport:
    row = db.get_run(run_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    return ReconciliationReport.model_validate_json(row["report_json"])
