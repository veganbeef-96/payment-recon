from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class Source(str, Enum):
    BANK = "bank"
    LEDGER = "ledger"


class Transaction(BaseModel):
    id: str
    source: Source
    posted_on: date
    amount: Decimal = Field(description="Signed amount; debits negative")
    reference: str = ""


class MatchStatus(str, Enum):
    MATCHED = "matched"
    UNMATCHED_BANK = "unmatched_bank"
    UNMATCHED_LEDGER = "unmatched_ledger"


class Match(BaseModel):
    status: MatchStatus
    bank_id: str | None = None
    ledger_id: str | None = None
    ledger_ids: list[str] = []
    score: float = 0.0


class ReconciliationReport(BaseModel):
    matches: list[Match]

    @property
    def matched_count(self) -> int:
        return sum(1 for m in self.matches if m.status is MatchStatus.MATCHED)
