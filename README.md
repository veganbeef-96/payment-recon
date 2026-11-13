# payment-recon

Reconciles bank statement CSVs against ledger export CSVs.

## Run

```bash
python -m venv .venv
. .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Use

`POST /reconcile` with two multipart files, `bank` and `ledger`:

```bash
curl -X POST http://127.0.0.1:8000/reconcile \
  -F bank=@samples/bank_debit_credit.csv \
  -F ledger=@samples/ledger.csv
```

The response lists each pair as `matched`, `unmatched_bank` or `unmatched_ledger`.

### CSV formats

Both files need a header row with `id` and `posted_on` (ISO date, `YYYY-MM-DD`), plus one of:

| Format | Columns | Sign |
| --- | --- | --- |
| Signed amount | `amount` | Negative for money out |
| Debit/credit | `debit`, `credit` | Money out goes in `debit` and money in goes in `credit`. Leave the other column empty. |

`reference` is optional. Other columns are ignored, and header names are not case-sensitive. If `amount` is present it wins over `debit`/`credit`.

Amounts can include currency symbols or codes and thousands separators. These all parse:

| Input | Value |
| --- | --- |
| `-120.00` | -120.00 |
| `$1,234.50` | 1234.50 |
| `1.234,50 €` | 1234.50 |
| `1234,50` | 1234.50 |
| `USD 99.00` | 99.00 |

When a value has both `,` and `.`, the one that comes last is the decimal separator. A single `,` followed by exactly three digits (`1,234`) is read as a thousands separator.

Sample files are in `samples/`: `bank.csv` and `ledger.csv` use `amount`, and `bank_debit_credit.csv` uses debit/credit.

### Errors

A file that can't be parsed returns `422` with a `detail` message. The first bad line stops the import.

| Problem | `detail` |
| --- | --- |
| Required column missing | `missing columns: ['amount (or debit and credit)']` |
| Amount not a number | `line 3: invalid amount 'abc'` |
| Debit and credit both blank | `line 4: debit and credit are both empty` |
| Bad date | `line 2: Invalid isoformat string: '02/11/2026'` |

Line numbers count the header as line 1. A missing `bank` or `ledger` file returns FastAPI's standard `422` validation error.

## Matching

Entries match when amounts are equal and dates are within 2 days. A shared reference adds to the score. Matching is greedy, highest score first.
