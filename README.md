# autoresearch-mlx

A fixed-time, single-metric autonomous research loop for transformer training on Apple Silicon, using [MLX](https://github.com/ml-explore/mlx). Edit one file, train for five minutes, let `val_bpb` decide what survives. A coding agent or a disciplined human can run this loop unsupervised.

This repository is a maintained fork of [`trevin-creator/autoresearch-mlx`](https://github.com/trevin-creator/autoresearch-mlx), which ported the training-loop slice of [`karpathy/autoresearch`](https://github.com/karpathy/autoresearch) from PyTorch/CUDA to MLX. This fork adds tooling, tests, and documentation on top. See [`NOTICE`](NOTICE) for full attribution.

---

## Table of contents

- [What this is](#what-this-is)
- [What this isn't](#what-this-isnt)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Smoke test](#smoke-test)
- [How the loop works](#how-the-loop-works)
- [What the MLX port changes](#what-the-mlx-port-changes)
- [Known limitations](#known-limitations)
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

## Requirements

- **Apple Silicon Mac.** Training runs on the GPU through MLX and Metal. There is no CPU or CUDA path.
- **Memory.** The default configuration (`DEPTH = 4`, `DEVICE_BATCH_SIZE = 16`, sequence length 2048) peaks at about 21 GB of unified memory during training; the depth-8 configuration it replaced peaked at about 27 GB (`memory_gb` column in `results.tsv`). 32 GB or more is comfortable. On a 16 GB machine, reduce `DEVICE_BATCH_SIZE` and `DEPTH` in `train.py` before the first run.
- **Disk.** `uv run prepare.py` downloads 10 training shards plus 1 pinned validation shard (about 92 MB each, roughly 1 GB total) to `~/.cache/autoresearch/` and trains the tokenizer there. `--num-shards` changes the count; `-1` fetches the full 6,542-shard dataset, which 5-minute runs do not need — the dataloader cycles epochs over whatever is present.
- **Python 3.10–3.13** (`requires-python >=3.10,<3.14`). With [uv](https://docs.astral.sh/uv/) no matching system Python is required: `uv sync` provisions an interpreter (it selected CPython 3.13.12 on a machine whose system Python was 3.14).
- **Rust toolchain** — only for the optional `bench-rs` CLI. Everything else runs without it.

Last verified 2026-07-17 on an Apple Silicon Mac with 128 GB unified memory: Python 3.13.12, mlx 0.31.0 (Metal available), numpy 2.4.2, polars 1.40.0, pyarrow 23.0.1, tiktoken 0.12.0, tokenizers 0.22.2, rustbpe 0.1.0. `make smoke`, `make test`, `make lint`, `make bench`, and `make bench-rs` all pass on that setup.

## Quick start

```bash
# 1. Install Python deps
make install

# 2. Verify the checkout (no downloads, no training)
make smoke

# 3. One-time data + tokenizer prep (~1 GB download)
uv run prepare.py

# 4. Run one 5-minute training experiment
uv run train.py

# 5. Summarize results
make bench
```

Common tasks are wrapped in the `Makefile`:

| Command | What it does |
|---|---|
| `make install` | Install Python deps via `uv` |
| `make smoke` | Fast repo verification — no data download, no training |
| `make test` | Run smoke tests (`pytest tests/`) |
| `make lint` | Run `ruff` |
| `make bench` | Render a markdown summary of `results.tsv` (Python, Polars-backed) |
| `make bench-rs` | Build and run the Rust sibling CLI |
| `make clean` | Remove build artifacts and caches |

## Smoke test

`scripts/smoke.sh` verifies a checkout without downloading data or spending the 5-minute budget. It prints the resolved environment, byte-compiles every module, imports the full dependency chain including MLX (via `prepare.py --help`), exercises `config.py` and all three `bench.py` subcommands, and runs the pytest suite.

```bash
make smoke        # or: bash scripts/smoke.sh
```

It does not train. The shortest real training invocation is `uv run prepare.py && uv run train.py` — data download and tokenizer training on the first call, then one full 5-minute experiment plus final eval (about 7 minutes total).

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

## What the MLX port changes

The port keeps upstream's model and protocol and replaces the framework machinery. Differences that matter, by module:

**`train.py`**

- All `torch`/CUDA machinery is removed; the model and loop are written against `mlx.core` and `mlx.nn`. Single process, unified memory. Peak memory comes from `mx.get_peak_memory()` instead of `torch.cuda.max_memory_allocated()`.
- **Optimizer.** Upstream trains 2-D matrix parameters with Muon (Newton–Schulz orthogonalization, NorMuon variance reduction, `torch.compile`d) inside a combined `MuonAdamW`. The port replaces this with a from-scratch per-parameter-group AdamW built on `mlx.utils.tree_flatten`, preserving upstream's per-group learning rates (embedding / unembedding / matrix / scalar, including the `(n_embd/768)^-0.5` model-dim scale). Muon itself is not ported; `train.py` marks it as future work.
- **No `torch.compile`, no autocast.** MLX evaluates lazily at explicit `mx.eval()` barriers. Weights are initialized in `bfloat16`, optimizer math runs in `float32`, and logits are computed in `float32` with the same `15·tanh(logits/15)` cap as upstream.
- **Attention** uses `mx.fast.scaled_dot_product_attention` with precomputed additive causal and sliding-window masks, cached per `(seq_len, window)` pair.
- **Defaults sized for a Mac:** `DEPTH` 8 → 4, `DEVICE_BATCH_SIZE` 128 → 16, `TOTAL_BATCH_SIZE` 2^19 → 2^16, as committed on this fork's `main` (see `results.tsv` for the walk that got there).

**`prepare.py`**

- Same dataset (`karpathy/climbmix-400b-shuffle`), same rustbpe-trained 8,192-entry tiktoken tokenizer, same BOS-aligned best-fit packing, same bits-per-byte evaluation.
- The dataloader yields plain `mx.array` int32 batches. Upstream's pinned-CPU-buffer / CUDA-buffer double-buffering does not exist here — unified memory makes host-to-device copies unnecessary. The `token_bytes` lookup is stored as a numpy `.npy` file instead of a `torch.save` tensor.
- `EVAL_TOKENS` is reduced from `40 * 524288` (~21M tokens) to `3 * 524288` (~1.6M) so the final eval finishes in about a minute on Apple Silicon. Consequence: **`val_bpb` values are not comparable with the CUDA upstream's** — compare only against your own baseline on your own hardware, as `program.md` instructs.

Unchanged from upstream: the fixed protocol constants (`MAX_SEQ_LEN = 2048`, `TIME_BUDGET = 300` s) and the model architecture — RoPE, `SSSL` sliding-window pattern, gated value embeddings on alternating layers (always including the last), learned residual/`x0` mixing scalars, ReLU² MLP, untied embeddings, logit cap.

## Known limitations

- AdamW only. Upstream's Muon path does not exist here, so matrix-parameter training dynamics differ from upstream results.
- `mfu_percent` in the run summary is a placeholder and always prints `0.00`.
- No checkpointing: a run's artifact is its `results.tsv` line, not weights. Nothing is saved for inference.
- Single device, single process. No distributed training.
- Python 3.14 is not yet supported (`requires-python <3.14`); `uv` provisions 3.13 automatically.

## Analysis and reporting

After a run, inspect results in either Python or Rust — both consume the same `results.tsv` and emit the same markdown:

```bash
# Python (Polars-backed)
uv run python bench.py summary   # full markdown summary + headline deltas
uv run python bench.py latest    # most recent run vs baseline
uv run python bench.py best      # lowest val_bpb

# Rust sibling
make bench-rs                    # build + run summary
```

See [`rust/bench-rs/README.md`](rust/bench-rs/README.md) and [`docs/adr/ADR-003-rust-scope.md`](docs/adr/ADR-003-rust-scope.md) for why both exist.

## Tests

`tests/test_smoke.py` covers imports, the `results.tsv` schema, and `bench.py`'s three subcommands. Training itself is not exercised — training is too slow and stateful for a smoke test, and its correctness is measured by `val_bpb` rather than assertions. `scripts/smoke.sh` wraps these tests together with byte-compilation and CLI checks.

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
- Smoke tests (`tests/`) and a no-training verification script (`scripts/smoke.sh`)
- System documentation (`ARCHITECTURE.md`)
- Rust-backed runtime dependencies (`polars`, `tokenizers`)
- Dev toolchain (`ruff`, `pytest`)
- Expanded `results.tsv` with apr20 runs

Thanks also to [@lati-cooki](https://github.com/lati-cooki) for ongoing support and encouragement.

## License

MIT. See [LICENSE](LICENSE).
