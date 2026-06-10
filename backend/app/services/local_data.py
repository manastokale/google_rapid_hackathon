"""Local CSV data access used for demos and development without BigQuery."""

import csv
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SEED_DIR = ROOT / "data" / "seed_data"


def _coerce(value: str) -> Any:
    if value == "":
        return ""
    if value in {"True", "False"}:
        return value == "True"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


@lru_cache
def load_table(table_name: str) -> list[dict[str, Any]]:
    path = SEED_DIR / f"{table_name}.csv"
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return [{key: _coerce(value) for key, value in row.items()} for row in csv.DictReader(f)]


def clear_cache() -> None:
    load_table.cache_clear()

