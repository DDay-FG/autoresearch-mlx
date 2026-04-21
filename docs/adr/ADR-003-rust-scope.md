# ADR-003: Rust Integration Scope

**Status:** Accepted
**Date:** 2026-04-20
**Deciders:** @DDay-FG

## Context

There is a cultural instinct, especially in fintech-adjacent engineering circles, to treat Rust as a signal of seriousness. Applied carelessly, this instinct leads to bad outcomes: rewriting functioning Python in Rust for no operational reason, fragmenting a project's language story, and — worst — breaking hard dependencies. MLX is Python-first. Apple's MLX team does not publish a Rust API; the community `mlx-rs` crate covers a small fraction of the Python surface area and is not Apple-maintained. Rewriting `train.py` in Rust would therefore break the training loop, invalidate every result in `results.tsv`, and produce a red flag rather than a signal.

At the same time, Rust can legitimately add value in places where Python pays an import-time or runtime cost out of proportion to its expressiveness benefit: CLI tools, static analyzers, data pipelines.

## Decision

Adopt a bounded Rust integration (**"Rust-1"** in internal shorthand):

1. **Rust-backed Python dependencies** where the Python API is still ergonomic: `polars`, `tokenizers`, the existing `rustbpe`, and the already-in-use `uv` installer. No API changes required.
2. **One first-party Rust CLI tool**: `rust/bench-rs/`, a sibling of `bench.py` that consumes the same `results.tsv` and emits the same markdown. This is where maintainer-authored Rust code lives in this repo.

Do **not**:
- Rewrite `train.py`, `prepare.py`, or any MLX-touching code in Rust.
- Create PyO3 bindings between Rust and Python in this repository. If a real need emerges later (e.g., a hot path in `prepare.py`), that will be a separate ADR.

## Options Considered

### Option A (Rust-0): No first-party Rust

| Pros | Cons |
|---|---|
| Zero toolchain burden | The fork has no authored Rust code; the "Rust where it helps" story has no artifact |

### Option B (Rust-1): `rust/bench-rs/` CLI sibling (chosen)

| Pros | Cons |
|---|---|
| Real Rust authored by the fork maintainer | Duplication with `bench.py` |
| The two implementations cross-check the log schema | Two codebases to maintain for one job |
| Zero risk to the training loop | Small binary size to manage |

### Option C (Rust-2): PyO3 bindings for a Python hot path

| Pros | Cons |
|---|---|
| Real speedups possible in the data pipeline | Fights MLX's Python-first nature; adds build complexity; months of real work |

### Option D (Rust-3): Rewrite `train.py` in Rust

Rejected. Breaks MLX integration. Rejected without further analysis.

## Trade-off Analysis

Option B is the smallest honest move. It puts actual maintainer-authored Rust in the tree, exercises a real Rust toolchain, and costs little. The duplication between `bench.py` and `bench-rs` is a feature: a divergence between the two is immediately flagged as a log schema issue.

## Consequences

- Contributors need a Rust toolchain to run `make bench-rs`. `make bench` (Python) works without Rust.
- `rust/bench-rs/target/` is git-ignored.
- If `results.tsv` ever grows columns, both implementations must be updated; a test should enforce parity of output over a fixture. (Deferred; small enough surface for now.)

## Action Items

- [x] Create `rust/bench-rs/Cargo.toml`, `src/main.rs`, `README.md`
- [x] Wire `make bench-rs` in the Makefile
- [x] Ignore `rust/*/target/` in `.gitignore`
- [ ] Consider adding a parity test between `bench.py` and `bench-rs` over a fixture TSV (future)
