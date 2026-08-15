# Contributing

Thanks for taking the time to contribute! 🍜

This is a personal-scale project, so the process is intentionally lightweight.

## Ground rules

- Open an issue before starting any non-trivial work — it's easier to align early than to rewrite a PR later.
- Keep PRs small and focused. One PR = one logical change.
- Every PR must pass CI (`pre-commit run --all-files`).
- Don't commit secrets. `.env` is git-ignored for a reason.

## Development setup

```bash
git clone https://github.com/bigit22/YazioNutritionIntegrator.git
cd YazioNutritionIntegrator

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pre-commit install

cp .env.example .env
# fill in tokens
```

## Code style

- Formatting: [Black](https://github.com/psf/black), line length 100
- Linting: [Ruff](https://github.com/astral-sh/ruff)
- Both run automatically via pre-commit

## Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/) loosely:

- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation only
- `chore:` — tooling, deps, refactors without behavior change
- `ci:` — CI / build changes

## Pull requests

- Target `main`
- Fill in the PR template
- Link related issues with `Fixes #N` — the issue will auto-close on merge
- Wait for green CI before merging
