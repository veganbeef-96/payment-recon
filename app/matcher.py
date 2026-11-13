from decimal import Decimal

from app.models import Match, MatchStatus, ReconciliationReport, Transaction
from app.rules import DEFAULT_RULES, MatchRules


def _amount_penalty(bank_amount: Decimal, ledger_amount: Decimal, rules: MatchRules) -> float | None:
    """Return 0..0.1 penalty for an amount difference, or None if out of tolerance."""
    if bank_amount == ledger_amount:
        return 0.0
    diff = abs(bank_amount - ledger_amount)
    # Never pair a debit with a credit, however small the difference.
    if diff > rules.amount_tolerance or (bank_amount < 0) != (ledger_amount < 0):
        return None
    return 0.1 * float(diff / rules.amount_tolerance)


def _score(bank: Transaction, ledger: Transaction, rules: MatchRules) -> float:
    penalty = _amount_penalty(bank.amount, ledger.amount, rules)
    if penalty is None:
        return 0.0
    gap = abs((bank.posted_on - ledger.posted_on).days)
    if gap > rules.date_tolerance_days:
        return 0.0
    date_part = 1.0 - gap / (rules.date_tolerance_days + 1)
    ref_part = rules.ref_bonus if bank.reference and bank.reference == ledger.reference else 0.0
    return max(0.0, min(1.0, 0.8 * date_part + ref_part) - penalty)


def reconcile(
    bank: list[Transaction],
    ledger: list[Transaction],
    rules: MatchRules = DEFAULT_RULES,
) -> ReconciliationReport:
    pairs = sorted(
        ((_score(b, l, rules), b, l) for b in bank for l in ledger),
        key=lambda p: p[0],
        reverse=True,
    )
    used_bank: set[str] = set()
    used_ledger: set[str] = set()
    matches: list[Match] = []

    for score, b, l in pairs:
        if score <= 0 or b.id in used_bank or l.id in used_ledger:
            continue
        used_bank.add(b.id)
        used_ledger.add(l.id)
        matches.append(Match(status=MatchStatus.MATCHED, bank_id=b.id, ledger_id=l.id, score=round(score, 3)))

    for b in bank:
        if b.id not in used_bank:
            matches.append(Match(status=MatchStatus.UNMATCHED_BANK, bank_id=b.id))
    for l in ledger:
        if l.id not in used_ledger:
            matches.append(Match(status=MatchStatus.UNMATCHED_LEDGER, ledger_id=l.id))

    return ReconciliationReport(matches=matches)
