import csv
import io
from datetime import date
from decimal import Decimal, InvalidOperation

from app.models import Source, Transaction

BASE_COLUMNS = {"id", "posted_on"}
DEBIT_CREDIT_COLUMNS = {"debit", "credit"}


def _parse_amount(value: str, column: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation:
        raise ValueError(f"invalid {column} {value!r}") from None


def _signed_amount(row: dict[str, str | None], use_debit_credit: bool) -> Decimal:
    if not use_debit_credit:
        return _parse_amount((row.get("amount") or "").strip(), "amount")

    debit = (row.get("debit") or "").strip()
    credit = (row.get("credit") or "").strip()
    if not debit and not credit:
        raise ValueError("debit and credit are both empty")
    # Banks write debits as positive or negative; either way they reduce the balance.
    out = abs(_parse_amount(debit, "debit")) if debit else Decimal(0)
    into = abs(_parse_amount(credit, "credit")) if credit else Decimal(0)
    return into - out


def parse_csv(text: str, source: Source) -> list[Transaction]:
    reader = csv.DictReader(io.StringIO(text))
    columns = {name.strip().lower() for name in reader.fieldnames or []}
    reader.fieldnames = [name.strip().lower() for name in reader.fieldnames or []]

    missing = BASE_COLUMNS - columns
    use_debit_credit = "amount" not in columns
    if use_debit_credit and not DEBIT_CREDIT_COLUMNS <= columns:
        missing.add("amount (or debit and credit)")
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")

    rows: list[Transaction] = []
    for line_no, row in enumerate(reader, start=2):
        try:
            rows.append(
                Transaction(
                    id=(row.get("id") or "").strip(),
                    source=source,
                    posted_on=date.fromisoformat((row.get("posted_on") or "").strip()),
                    amount=_signed_amount(row, use_debit_credit),
                    reference=(row.get("reference") or "").strip(),
                )
            )
        except (ValueError, InvalidOperation) as exc:
            raise ValueError(f"line {line_no}: {exc}") from exc
    return rows
