from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class MatchRules:
    # Max days between bank and ledger dates for a match.
    date_tolerance_days: int = 2
    # Max absolute amount difference still treated as a match.
    amount_tolerance: Decimal = Decimal("0.00")
    # Score added when references are equal and non-empty.
    ref_bonus: float = 0.2


DEFAULT_RULES = MatchRules()
