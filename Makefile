
.PHONY: dev routes schema test

dev:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

routes:
	uv run python scripts/print_routes.py

schema:
	uv run python scripts/inspect_db.py

test:
	uv run pytest
