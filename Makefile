ruff:
	uv run ruff check .

mypy:
	uv run mypy .

check: ruff mypy