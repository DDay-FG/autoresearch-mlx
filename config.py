"""Read hyperparameter constants from train.py without executing it.

train.py is the single source of truth for experiment hyperparameters
(the autoresearch loop only edits train.py). This module exposes those
values to read-only tools (bench.py, the test suite, analysis scripts)
via static AST parsing — train.py is never imported or executed.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent
TRAIN_PY = REPO_ROOT / "train.py"


def load_train_config(path: Path | str = TRAIN_PY) -> dict[str, Any]:
    """Return every module-level ``NAME = literal`` assignment from
    ``path`` where ``NAME`` is UPPERCASE.

    Only literal values are extracted (numbers, strings, tuples, lists,
    dicts, booleans, None). Non-literal right-hand sides are skipped.
    The source is parsed as text; it is never executed.
    """
    source = Path(path).read_text()
    tree = ast.parse(source)
    config: dict[str, Any] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not (isinstance(target, ast.Name) and target.id.isupper()):
                continue
            try:
                config[target.id] = ast.literal_eval(node.value)
            except (ValueError, SyntaxError):
                # skip constants whose RHS isn't a plain literal
                pass
    return config


def _cli() -> None:
    cfg = load_train_config()
    if not cfg:
        print("(no uppercase literal constants found in train.py)")
        return
    width = max(len(k) for k in cfg)
    for k, v in cfg.items():
        print(f"{k:<{width}} = {v!r}")


if __name__ == "__main__":
    _cli()
