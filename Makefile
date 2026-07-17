# autoresearch-mlx — common task wrappers.
#
# This Makefile is for human convenience; the autonomous loop itself
# still runs `uv run train.py` directly per program.md.

.PHONY: help install smoke test lint bench bench-rs clean

help:
	@echo "Targets:"
	@echo "  make install   - install Python deps via uv"
	@echo "  make smoke     - fast repo verification (no data download, no training)"
	@echo "  make test      - run smoke tests"
	@echo "  make lint      - run ruff"
	@echo "  make bench     - render markdown summary of results.tsv (Python)"
	@echo "  make bench-rs  - build and run the Rust sibling CLI"
	@echo "  make clean     - remove build artifacts and caches"

install:
	uv sync

smoke:
	bash scripts/smoke.sh

test:
	uv run pytest tests/ -q

lint:
	uv run ruff check .

bench:
	uv run python bench.py summary

bench-rs:
	cd rust/bench-rs && cargo build --release --quiet
	./rust/bench-rs/target/release/bench-rs --results results.tsv summary

clean:
	rm -rf rust/bench-rs/target
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
