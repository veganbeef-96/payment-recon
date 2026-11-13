# Project rules: payment-recon

## Git
- Identity is set in repo-local config: `user.name` = veganbeef-96, `user.email` = 232722682+veganbeef-96@users.noreply.github.com. Do not change it.
- Commit messages use Conventional Commits (`feat:`, `fix:`, `refactor:`, `docs:`, `chore:`).
- Subject is imperative and at most 72 characters.
- Do not add `Co-Authored-By` or any other AI attribution trailer.
- Commit dates are the real date the work is done. Never set `GIT_AUTHOR_DATE` or `GIT_COMMITTER_DATE` to a past date.
- Push to `main` after each commit.

## Code
- Python 3.11+, FastAPI, Pydantic v2.
- Code must run. Keep it working at every commit.
- No test files or test scripts in this repo.
- Comments are at most 2 lines per comment block.
- Do not commit secrets, `.env` files, or bank data. Use sample CSVs only.
