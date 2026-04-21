# bench-rs

Rust sibling of `bench.py`. Consumes `results.tsv` from the repository root and emits the same three markdown reports.

## Why it exists

See `../../docs/adr/ADR-003-rust-scope.md`. In short: two independent implementations over one log schema catches drift cheaply; the Rust binary has zero import-time cost; and it gives this fork some honestly-authored Rust code in the tree.

## Build

```bash
cd rust/bench-rs && cargo build --release
```

The binary lands at `rust/bench-rs/target/release/bench-rs`.

## Usage

```bash
./target/release/bench-rs --results ../../results.tsv summary
./target/release/bench-rs --results ../../results.tsv latest
./target/release/bench-rs --results ../../results.tsv best
```

From the repository root, `make bench-rs` does the build-and-run in one step.

## Parity

`bench-rs` and `bench.py` should produce identical markdown for the same input TSV. If they diverge, either the log schema grew a column or one of the implementations has a bug. A fixture-based parity test is on the roadmap (see ADR-003 action items).
