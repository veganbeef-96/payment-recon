from fastapi import FastAPI, File, HTTPException, Response, UploadFile
from fastapi.concurrency import run_in_threadpool

from app import db
from app.csv_import import parse_csv
from app.matcher import reconcile
from app.models import ReconciliationReport, Source
from app.store_routes import router as store_router

app = FastAPI(title="payment-recon")
app.include_router(store_router)


async def _read_upload(upload: UploadFile, source: Source):
    raw = (await upload.read()).decode("utf-8-sig")
    try:
        return parse_csv(raw, source)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/reconcile", response_model=ReconciliationReport)
async def reconcile_files(
    response: Response,
    bank: UploadFile = File(..., description="Bank statement CSV"),
    ledger: UploadFile = File(..., description="Ledger export CSV"),
) -> ReconciliationReport:
    bank_rows = await _read_upload(bank, Source.BANK)
    ledger_rows = await _read_upload(ledger, Source.LEDGER)
    report = reconcile(bank_rows, ledger_rows)
    # sqlite3 is blocking, so keep the write off the event loop.
    run_id = await run_in_threadpool(db.save_run, report.model_dump_json())
    response.headers["X-Run-Id"] = str(run_id)
    return report
