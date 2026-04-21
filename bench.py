"""Analyze results.tsv and emit a markdown summary.

Usage:
    python bench.py summary         # full markdown table + headline deltas
    python bench.py latest          # most recent run vs baseline
    python bench.py best            # the single row with lowest val_bpb

The only heavy dependency is Polars; everything else is stdlib. Output
is plain markdown so it drops cleanly into a README, a PR description,
or a terminal.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

RESULTS = Path(__file__).resolve().parent / "results.tsv"
REQUIRED_COLUMNS = {"commit", "val_bpb", "memory_gb", "status", "description"}


def load(path: Path = RESULTS) -> pl.DataFrame:
    if not path.exists():
        sys.exit(f"bench: results.tsv not found at {path}")
    df = pl.read_csv(path, separator="\t")
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        sys.exit(f"bench: results.tsv is missing required columns: {sorted(missing)}")
    if df.height == 0:
        sys.exit("bench: results.tsv has no rows")
    return df


def _improvement_pct(baseline_val: float, new_val: float) -> float:
    return 100.0 * (baseline_val - new_val) / baseline_val


def cmd_summary(df: pl.DataFrame) -> None:
    baseline = df.row(0, named=True)
    best = df.sort("val_bpb").row(0, named=True)
    kept = df.filter(pl.col("status") == "keep").height
    discarded = df.filter(pl.col("status") == "discard").height
    delta = _improvement_pct(baseline["val_bpb"], best["val_bpb"])

    print("# autoresearch-mlx — experiment summary\n")
    print(f"- Runs logged: **{df.height}** (kept: {kept}, discarded: {discarded})")
    print(f"- Baseline: `{baseline['commit']}` · val_bpb `{baseline['val_bpb']:.6f}`")
    print(f"- Best:     `{best['commit']}` · val_bpb `{best['val_bpb']:.6f}`")
    print(f"- Improvement over baseline: **{delta:.2f}%**\n")

    print("## All runs\n")
    print("| Commit | val_bpb | Status | Description |")
    print("|---|---:|---|---|")
    for row in df.iter_rows(named=True):
        print(
            f"| `{row['commit']}` | {row['val_bpb']:.6f} | {row['status']} | "
            f"{row['description']} |"
        )


def cmd_latest(df: pl.DataFrame) -> None:
    last = df.row(df.height - 1, named=True)
    first = df.row(0, named=True)
    delta = _improvement_pct(first["val_bpb"], last["val_bpb"])
    print(
        f"Latest: `{last['commit']}`  val_bpb {last['val_bpb']:.6f}  ({last['status']})"
    )
    print(
        f"  vs baseline `{first['commit']}` ({first['val_bpb']:.6f}): {delta:+.2f}%"
    )
    print(f"  note: {last['description']}")


def cmd_best(df: pl.DataFrame) -> None:
    best = df.sort("val_bpb").row(0, named=True)
    print(f"Best: `{best['commit']}`  val_bpb {best['val_bpb']:.6f}  ({best['status']})")
    print(f"  note: {best['description']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze results.tsv and emit a markdown summary.",
    )
    parser.add_argument(
        "command",
        choices=["summary", "latest", "best"],
        help="what to print",
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=RESULTS,
        help="path to results.tsv (default: repo root)",
    )
    args = parser.parse_args()
    df = load(args.results)
    {"summary": cmd_summary, "latest": cmd_latest, "best": cmd_best}[args.command](df)


if __name__ == "__main__":
    main()
