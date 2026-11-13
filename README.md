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

`POST /reconcile` with two multipart files, `bank` and `ledger`. Each CSV needs the columns `id`, `posted_on` (ISO date), `amount` (negative for debits), and optionally `reference`.

Sample files are in `samples/`.

## Matching

Entries match when amounts are equal and dates are within 2 days. A shared reference adds to the score. Matching is greedy, highest score first.
