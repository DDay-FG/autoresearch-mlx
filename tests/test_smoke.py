"""Smoke tests — verify imports and basic invariants without running training.

Run with:
    uv run pytest tests/ -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import polars as pl
import pytest

REPO = Path(__file__).resolve().parent.parent

# ensure repo root is importable (config.py, bench.py live there)
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def test_config_module_imports():
    import config  # noqa: F401


def test_bench_module_imports():
    import bench  # noqa: F401


def test_config_extracts_uppercase_constants():
    """config.load_train_config() returns a dict of train.py's UPPERCASE literals."""
    from config import load_train_config

    cfg = load_train_config()
    assert isinstance(cfg, dict)
    assert len(cfg) > 0, "expected at least one uppercase literal in train.py"
    # every key must be all-caps
    assert all(k == k.upper() for k in cfg), "non-uppercase key leaked into config"


def test_results_tsv_schema():
    """results.tsv has the expected header columns and at least one row."""
    df = pl.read_csv(REPO / "results.tsv", separator="\t")
    assert set(df.columns) == {
        "commit",
        "val_bpb",
        "memory_gb",
        "status",
        "description",
    }
    assert df.height > 0


def test_results_tsv_numeric_columns():
    """val_bpb and memory_gb parse as floats without errors."""
    df = pl.read_csv(REPO / "results.tsv", separator="\t")
    assert df.schema["val_bpb"] in (pl.Float32, pl.Float64)
    assert df.schema["memory_gb"] in (pl.Float32, pl.Float64)


def test_results_tsv_status_values():
    """status column only contains 'keep' or 'discard'."""
    df = pl.read_csv(REPO / "results.tsv", separator="\t")
    statuses = set(df["status"].to_list())
    assert statuses <= {"keep", "discard"}, f"unexpected status values: {statuses}"


def test_bench_load_succeeds():
    """bench.load() returns a polars DataFrame."""
    from bench import load

    df = load(REPO / "results.tsv")
    assert df.height > 0
    assert "val_bpb" in df.columns


@pytest.mark.parametrize("cmd", ["summary", "latest", "best"])
def test_bench_commands_smoke(cmd, capsys):
    """Each bench subcommand produces some output without raising."""
    from bench import cmd_best, cmd_latest, cmd_summary, load

    df = load(REPO / "results.tsv")
    {"summary": cmd_summary, "latest": cmd_latest, "best": cmd_best}[cmd](df)
    out = capsys.readouterr().out
    assert len(out) > 0
