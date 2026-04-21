# autoresearch-mlx

A fixed-time, single-metric autonomous research loop for transformer training on Apple Silicon, using [MLX](https://github.com/ml-explore/mlx). Edit one file, train for five minutes, let `val_bpb` decide what survives. A coding agent or a disciplined human can run this loop unsupervised.

This repository is a maintained fork of [`trevin-creator/autoresearch-mlx`](https://github.com/trevin-creator/autoresearch-mlx) with additional tooling, tests, and documentation added on top. See [`NOTICE`](NOTICE) for full attribution.

---

## Table of contents

- [What this is](#what-this-is)
- [What this isn't](#what-this-isnt)
- [Quick start](#quick-start)
- [How the loop works](#how-the-loop-works)
- [Analysis and reporting](#analysis-and-reporting)
- [Tests](#tests)
- [Recent runs (Apr 2026)](#recent-runs-apr-2026)
- [Architecture and ADRs](#architecture-and-adrs)
- [Lineage](#lineage)
- [License](#license)

## What this is

A minimal harness for running Karpathy-style autonomous experiment loops on Apple Silicon. One mutable file, one metric, a fixed time budget, a clean keep-or-revert history. Point a coding agent at `program.md` and it runs itself.

**It saves time if** you want to iterate on transformer training ideas on Apple Silicon without touching CUDA or PyTorch, and you care about wall-clock iteration speed over MFU.

## What this isn't

- Not a production training framework — it's an experiment scaffold
- Not a fine-tuning toolkit — every run trains cold from scratch
- Not MFU-optimized — reporting is a placeholder; compare runs by `val_bpb`
- Not a full nanochat port — only the training-loop slice is lifted, not tokenizers-at-scale, RLHF, or serving
- Not benchmarked against CUDA rigs — the point is iteration speed on a Mac you already own

## Quick start

Requirements: Apple Silicon Mac, Python 3.10+, [uv](https://docs.astral.sh/uv/), and — for `bench-rs` only — a stable Rust toolchain.

```bash
# 1. Install Python deps
make install

# 2. One-time data + tokenizer prep
uv run prepare.py

# 3. Run one 5-minute training experiment
uv run train.py

# 4. Summarize results
make bench
```

Common tasks are wrapped in the `Makefile`:

| Command | What it does |
|---|---|
| `make install` | Install Python deps via `uv` |
| `make test` | Run smoke tests (`pytest tests/`) |
| `make lint` | Run `ruff` |
| `make bench` | Render a markdown summary of `results.tsv` (Python, Polars-backed) |
| `make bench-rs` | Build and run the Rust sibling CLI |
| `make clean` | Remove build artifacts and caches |

## How the loop works

Full protocol in [`program.md`](program.md). System layering in [`ARCHITECTURE.md`](ARCHITECTURE.md). Short version:

| File | Role | Mutable in the loop? |
|---|---|---|
| `program.md` | Protocol the agent follows | No |
| `train.py` | Model + training loop — the one editable file | **Yes** |
| `prepare.py` | Data pipeline + evaluation | No |
| `config.py` | Read-only view of `train.py` constants via AST parse | No |
| `results.tsv` | Append-only experiment log | Append only |
| `bench.py` / `rust/bench-rs/` | Analysis siblings | No |
| `tests/` | Smoke tests for non-training invariants | No |

The loop: edit `train.py`, run a 5-minute experiment, read `val_bpb`, keep if better, revert if not, append to `results.tsv`, repeat.

## Analysis and reporting

After a run, inspect results in either Python or Rust — both consume the same `results.tsv` and emit the same markdown:

```bash
# Python (Polars-backed)
python bench.py summary   # full markdown summary + headline deltas
python bench.py latest    # most recent run vs baseline
python bench.py best      # lowest val_bpb

# Rust sibling
make bench-rs             # build + run summary
```

See [`rust/bench-rs/README.md`](rust/bench-rs/README.md) and [`docs/adr/ADR-003-rust-scope.md`](docs/adr/ADR-003-rust-scope.md) for why both exist.

## Tests

`tests/test_smoke.py` covers imports, the `results.tsv` schema, and `bench.py`'s three subcommands. Training itself is not exercised — training is too slow and stateful for a smoke test, and its correctness is measured by `val_bpb` rather than assertions.

```bash
make test
```

## Recent runs (Apr 2026)

Continued exploration on this fork. Baseline retraced on current hardware (`1.804532`), then pushed down through batch-size tuning and an activation change.

| Step | val_bpb | Note |
|---|---:|---|
| Baseline | 1.804532 | apr20, this hardware |
| Batch floor search | 1.438082 | 2^13 wins; 2^12 regresses on gradient noise |
| SiLU activation | 1.416715 | apr20 best (-21.5% vs apr20 baseline) |

Headline finding for this model size on Apple Silicon: with a fixed 5-minute budget, step count dominates. Halving the batch compounds into meaningful wins until gradient noise takes over around 2^13 (~8K tokens). Working branch is not pushed to this repo.

The upstream `results.tsv` walk (four rows, commits `383abb4` → `5efc7aa`) remains in the log for provenance.

## Architecture and ADRs

Read [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full system layering. Decisions governing this fork's evolution live under [`docs/adr/`](docs/adr/):

- [`ADR-001`](docs/adr/ADR-001-attribution.md) — Attribution strategy
- [`ADR-002`](docs/adr/ADR-002-dependencies.md) — Dependency upgrade scope
- [`ADR-003`](docs/adr/ADR-003-rust-scope.md) — Rust integration scope

## Lineage

This repository began as a downstream of [`trevin-creator/autoresearch-mlx`](https://github.com/trevin-creator/autoresearch-mlx). Full attribution to the upstream author and to the conceptual lineage — Karpathy's autoresearch protocol, `scasella/nanochat-mlx`'s MLX GPT patterns, `awni/picochat`'s MLX training patterns, and Apple's MLX team — is in [`NOTICE`](NOTICE). Every commit in this repository's git log preserves its contributor's authorship.

What this fork adds on top:

- Explicit attribution (`NOTICE`) and documented decisions (`docs/adr/`)
- Analysis layer (`bench.py` in Python, `rust/bench-rs/` in Rust)
- Configuration access (`config.py`)
- Smoke tests (`tests/`)
- System documentation (`ARCHITECTURE.md`)
- Rust-backed runtime dependencies (`polars`, `tokenizers`)
- Dev toolchain (`ruff`, `pytest`)
- Expanded `results.tsv` with apr20 runs

Thanks also to [@lati-cooki](https://github.com/lati-cooki) for ongoing support and encouragement.

## License

MIT. See [LICENSE](LICENSE).
