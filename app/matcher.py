from decimal import Decimal
from itertools import combinations

from app.models import Match, MatchStatus, ReconciliationReport, Transaction
from app.rules import DEFAULT_RULES, MatchRules

# Split matching tries groups of 2..MAX_SPLIT_GROUP ledger lines.
# Candidates per bank line are capped so the search stays bounded.
MAX_SPLIT_GROUP = 3
MAX_SPLIT_CANDIDATES = 12
# Split matches are less certain than one-to-one matches.
SPLIT_CONFIDENCE = 0.9


def _amount_penalty(bank_amount: Decimal, ledger_amount: Decimal, rules: MatchRules) -> float | None:
    """Return 0..0.1 penalty for an amount difference, or None if out of tolerance."""
    if bank_amount == ledger_amount:
        return 0.0
    diff = abs(bank_amount - ledger_amount)
    # Never pair a debit with a credit, however small the difference.
    if diff > rules.amount_tolerance or (bank_amount < 0) != (ledger_amount < 0):
        return None
    return 0.1 * float(diff / rules.amount_tolerance)


def _date_part(bank: Transaction, ledger: Transaction, rules: MatchRules) -> float | None:
    gap = abs((bank.posted_on - ledger.posted_on).days)
    if gap > rules.date_tolerance_days:
        return None
    return 1.0 - gap / (rules.date_tolerance_days + 1)


def _ref_matches(bank: Transaction, ledger: Transaction) -> bool:
    return bool(bank.reference) and bank.reference == ledger.reference


def _score(bank: Transaction, ledger: Transaction, rules: MatchRules) -> float:
    penalty = _amount_penalty(bank.amount, ledger.amount, rules)
    date_part = _date_part(bank, ledger, rules)
    if penalty is None or date_part is None:
        return 0.0
    ref_part = rules.ref_bonus if _ref_matches(bank, ledger) else 0.0
    return max(0.0, min(1.0, 0.8 * date_part + ref_part) - penalty)


def _split_score(bank: Transaction, group: tuple[Transaction, ...], rules: MatchRules) -> float:
    penalty = _amount_penalty(bank.amount, sum((l.amount for l in group), Decimal(0)), rules)
    if penalty is None:
        return 0.0
    date_part = sum(_date_part(bank, l, rules) for l in group) / len(group)
    ref_part = rules.ref_bonus if any(_ref_matches(bank, l) for l in group) else 0.0
    return max(0.0, SPLIT_CONFIDENCE * min(1.0, 0.8 * date_part + ref_part) - penalty)


def _best_split(
    bank: Transaction, ledger: list[Transaction], rules: MatchRules
) -> tuple[float, tuple[Transaction, ...]] | None:
    """Find the smallest, then best-scoring, group of ledger lines summing to bank."""
    candidates = [
        l
        for l in ledger
        if _date_part(bank, l, rules) is not None and (l.amount < 0) == (bank.amount < 0)
    ]
    candidates.sort(key=lambda l: (abs((bank.posted_on - l.posted_on).days), l.id))
    candidates = candidates[:MAX_SPLIT_CANDIDATES]

    for size in range(2, MAX_SPLIT_GROUP + 1):
        scored = [(_split_score(bank, g, rules), g) for g in combinations(candidates, size)]
        scored = [s for s in scored if s[0] > 0]
        if scored:
            return max(scored, key=lambda s: s[0])
    return None


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
        if b.id in used_bank:
            continue
        found = _best_split(b, [l for l in ledger if l.id not in used_ledger], rules)
        if found is None:
            continue
        score, group = found
        used_bank.add(b.id)
        used_ledger.update(l.id for l in group)
        # Interim: one row per ledger line until Match gains ledger_ids.
        for l in group:
            matches.append(Match(status=MatchStatus.MATCHED, bank_id=b.id, ledger_id=l.id, score=round(score, 3)))

    for b in bank:
        if b.id not in used_bank:
            matches.append(Match(status=MatchStatus.UNMATCHED_BANK, bank_id=b.id))
    for l in ledger:
        if l.id not in used_ledger:
            matches.append(Match(status=MatchStatus.UNMATCHED_LEDGER, ledger_id=l.id))

    return ReconciliationReport(matches=matches)
