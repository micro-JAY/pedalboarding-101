#!/usr/bin/env python3
"""Load Surge XT and export its parameter table."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


SEARCH_GROUPS = [
    ("filter", "cutoff"),
    ("filter", "res"),
    ("osc",),
    ("attack",),
    ("release",),
    ("volume",),
    ("level",),
]


def main() -> int:
    from pedalboard_surge_utils import (
        ensure_output_dirs,
        load_surge,
        parameter_table,
        plugin_metadata,
        print_parameter_matches,
        write_parameter_table_csv,
    )

    dirs = ensure_output_dirs(ROOT)
    try:
        surge = load_surge(initialization_timeout=30.0)
    except Exception as exc:
        print(f"Unable to load Surge XT: {type(exc).__name__}: {exc}")
        return 1

    print("Loaded Surge XT plugin metadata:")
    for key, value in plugin_metadata(surge).items():
        print(f"  {key}: {value}")

    rows = parameter_table(surge)
    output_path = dirs["analysis"] / "surge_parameters.csv"
    write_parameter_table_csv(rows, output_path)
    print(f"\nExported {len(rows)} parameters to {output_path}")

    print("\nUseful exploratory searches:")
    for terms in SEARCH_GROUPS:
        print(f"\nterms={terms!r}")
        print_parameter_matches(surge, terms, max_results=8)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
