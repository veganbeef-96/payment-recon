from app.models import Match, MatchStatus, ReconciliationReport, Transaction
from app.rules import DEFAULT_RULES, MatchRules


def _score(bank: Transaction, ledger: Transaction, rules: MatchRules) -> float:
    if bank.amount != ledger.amount:
        return 0.0
    gap = abs((bank.posted_on - ledger.posted_on).days)
    if gap > rules.date_tolerance_days:
        return 0.0
    date_part = 1.0 - gap / (rules.date_tolerance_days + 1)
    ref_part = rules.ref_bonus if bank.reference and bank.reference == ledger.reference else 0.0
    return min(1.0, 0.8 * date_part + ref_part)


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
