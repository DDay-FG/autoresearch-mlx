# Architecture

## Purpose

`autoresearch-mlx` is a minimal harness that lets a coding agent (or a disciplined human) run Karpathy-style fixed-time training experiments on Apple Silicon. One file carries all experimental variation; the rest of the repository is stable scaffolding; results accumulate in a single append-only log.

## Layering

```
  ┌─────────────────────────────────────────────────────┐
  │               program.md  (protocol)                │
  │         autonomous experiment loop rules            │
  └────────────────────────┬────────────────────────────┘
                           │ drives
  ┌────────────────────────▼────────────────────────────┐
  │          train.py  (mutable experiment layer)       │
  │   model + optimizer + loop; edited per experiment   │
  └────────────────────────┬────────────────────────────┘
                           │ calls
  ┌────────────────────────▼────────────────────────────┐
  │          prepare.py  (stable data layer)            │
  │      tokenizer, data pipeline, evaluate_bpb         │
  └────────────────────────┬────────────────────────────┘
                           │ writes results to
  ┌────────────────────────▼────────────────────────────┐
  │           results.tsv  (append-only log)            │
  │   commit · val_bpb · memory_gb · status · desc      │
  └────────────────────────┬────────────────────────────┘
                           │ consumed by
  ┌────────────────────────▼────────────────────────────┐
  │          bench.py   and   rust/bench-rs/            │
  │        analysis, comparison, reporting              │
  └─────────────────────────────────────────────────────┘
```

## The autoresearch rule

Only `train.py` is modified during an experiment. Everything else is stable surface. This constraint makes `git` the natural experiment tracker — each commit on an experiment branch is one experiment, and `val_bpb` plus `results.tsv` tell you which branch was a keeper.

## Components

| File | Purpose | Mutable in the loop? |
|---|---|---|
| `program.md` | Protocol the agent follows | Read-only |
| `train.py` | Model + training loop | **Yes — the only editable file** |
| `prepare.py` | Data pipeline + evaluation | Read-only |
| `config.py` | Read-only view of `train.py` constants via AST parse | Read-only |
| `bench.py` | Python analysis CLI (uses Polars) | Read-only |
| `rust/bench-rs/` | Rust analysis CLI (sibling of `bench.py`) | Read-only |
| `tests/` | Smoke tests — imports, schema, roundtrips | Read-only |
| `results.tsv` | Experiment log | Append only |
| `docs/adr/` | Architecture decision records | Append only |

## The analysis layer

`bench.py` (Python) and `rust/bench-rs/` (Rust) both consume `results.tsv` and emit the same markdown summaries. They exist as a pair for three reasons:

1. The Rust binary has zero import-time cost — useful in scripts, CI, or anywhere a Python interpreter is overkill.
2. Two independent implementations against the same log schema is a cheap consistency check: if they disagree, the schema has drifted or one has a bug.
3. Python is the canonical language for MLX work; Rust is where sharp tooling lives. Keeping both honest about the same log keeps them both honest.

Neither is "primary." The Python tool is easier to extend; the Rust tool is leaner at runtime.

## Downstream additions (this fork)

Compared to the upstream `trevin-creator/autoresearch-mlx`, this fork adds the layers below `results.tsv` — reporting, tests, configuration access, and an architecture vocabulary (`ARCHITECTURE.md`, `docs/adr/`). The autoresearch core (`program.md`, `train.py`, `prepare.py`) remains substantially as the upstream author wrote it, with the expected per-experiment drift on `train.py`.

## Reading order

1. This file — architecture and why
2. `README.md` — how to run
3. `program.md` — what the agent does during an experiment
4. `docs/adr/` — governing decisions
5. `NOTICE` — full attribution lineage
