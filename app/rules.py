from dataclasses import dataclass


@dataclass(frozen=True)
class MatchRules:
    # Max days between bank and ledger dates for a match.
    date_tolerance_days: int = 2
    # Score added when references are equal and non-empty.
    ref_bonus: float = 0.2


DEFAULT_RULES = MatchRules()
