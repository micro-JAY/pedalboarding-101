#!/usr/bin/env python3
"""Print the tutorial environment and verify required imports."""

from __future__ import annotations

import sys
from pathlib import Path
import os


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache" / "matplotlib"))
(ROOT / ".cache" / "matplotlib").mkdir(parents=True, exist_ok=True)


def main() -> int:
    required_imports = ["numpy", "matplotlib", "mido", "pedalboard"]
    failures: list[str] = []

    for module_name in required_imports:
        try:
            __import__(module_name)
        except Exception as exc:
            failures.append(f"{module_name}: {type(exc).__name__}: {exc}")

    if failures:
        print("Required import failures:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    from pedalboard_surge_utils import (
        discover_surge_candidates,
        ensure_output_dirs,
        print_environment_summary,
    )

    ensure_output_dirs(ROOT)
    print_environment_summary()
    if sys.version_info[:2] != (3, 12):
        print(
            "Note: this tutorial can run outside Python 3.12, but PPv2's "
            "long-term target is Python 3.12."
        )

    print("\nDiscovered Surge XT candidates:")
    candidates = discover_surge_candidates(scan_plugin_names=False)
    if not candidates:
        print("  none")
    for candidate in candidates:
        print(f"  - {candidate.path} [{candidate.plugin_format}]")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
