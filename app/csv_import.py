import csv
import io
from datetime import date
from decimal import Decimal, InvalidOperation

from app.models import Source, Transaction

REQUIRED_COLUMNS = {"id", "posted_on", "amount"}


def parse_csv(text: str, source: Source) -> list[Transaction]:
    reader = csv.DictReader(io.StringIO(text))
    missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")

    rows: list[Transaction] = []
    for line_no, row in enumerate(reader, start=2):
        try:
            rows.append(
                Transaction(
                    id=row["id"].strip(),
                    source=source,
                    posted_on=date.fromisoformat(row["posted_on"].strip()),
                    amount=Decimal(row["amount"].strip()),
                    reference=(row.get("reference") or "").strip(),
                )
            )
        except (ValueError, InvalidOperation) as exc:
            raise ValueError(f"line {line_no}: {exc}") from exc
    return rows
