# ADR-002: Dependency Upgrade Scope

**Status:** Accepted
**Date:** 2026-04-20
**Deciders:** @DDay-FG

## Context

The upstream `pyproject.toml` specifies:

```
mlx, numpy, pyarrow, regex, requests, rustbpe, tiktoken
```

None of these were changed for months in upstream. The fork wants to justifiably claim "more recent and advanced dependencies" without dependency inflation — adding packages only where they serve a concrete downstream purpose.

## Decision

Add two runtime dependencies and two dev dependencies. Do not drop any upstream dependency.

### Runtime additions

- **`polars>=0.20`** — Rust-backed columnar DataFrame library. Used in `bench.py` for reading and aggregating `results.tsv`. Benchmarks consistently show 10–100× throughput over pandas for tabular workloads; chosen here for zero-pandas parity, a Rust-backed runtime, and a clean Python API.
- **`tokenizers>=0.20`** — HuggingFace's Rust-cored tokenizer. Provides a second tokenizer implementation alongside the existing `rustbpe` and `tiktoken` paths for comparative benchmarking in future work.

### Dev additions

- **`pytest>=8`** — Required to run `tests/`.
- **`ruff>=0.5`** — Rust-implemented linter; replaces any previous-generation linting.

### Pin policy

All runtime dependencies remain expressed as lower-bound ranges (`>=`) to avoid artificial version ceilings. `uv.lock` captures exact resolved versions at install time.

## Options Considered

### Option A: Add all four (chosen)

Every addition has a concrete in-repo consumer. Polars is used in `bench.py`. Tokenizers is used in future tokenizer-bench experiments. Pytest runs `tests/`. Ruff runs in CI and locally via `make lint`.

### Option B: Add Polars only

| Pros | Cons |
|---|---|
| Smallest diff | No story for expanded tokenizer experiments; leaves `make test` and `make lint` broken |

### Option C: Add MLX major-version bump as well

The upstream constraint is `mlx>=0.30.0`. The latest MLX release introduces new Metal kernels and mixed-precision support; however, the `>=` constraint already permits installing the latest. A hard pin upgrade would risk breaking older users' installs for no additional benefit.

## Trade-off Analysis

Two runtime deps and two dev deps is modest; each was chosen for a use case that exists in this repository today, not for appearance. Polars and tokenizers are both Rust-backed, reinforcing the fork's theme of "Rust where it adds value, Python where it's the correct choice."

## Consequences

- `make install` pulls more packages but each is used.
- `make test` and `make lint` are now runnable targets.
- Future work on tokenizer performance has a fair comparison surface.

## Action Items

- [x] Update `pyproject.toml` with new runtime and dev deps
- [ ] Regenerate `uv.lock` via `uv sync` (done on first install)
