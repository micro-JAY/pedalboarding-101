#!/usr/bin/env python3
"""Smoke-test the Surge XT render path used by the notebook."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


PARAMETER_SEARCH_TERMS = [
    "cutoff",
    "filter",
    "resonance",
    "volume",
    "level",
    "attack",
    "release",
    "osc",
    "scene",
]


def main() -> int:
    from pedalboard_surge_utils import (
        SAMPLE_RATE,
        assert_render_is_sane,
        dbfs,
        ensure_output_dirs,
        likely_continuous_parameters,
        load_surge,
        mean_absolute_difference,
        render_note,
        try_parameter_change,
        write_audio,
    )

    dirs = ensure_output_dirs(ROOT)
    try:
        surge = load_surge(initialization_timeout=30.0)
    except Exception as exc:
        print(f"Unable to load Surge XT: {type(exc).__name__}: {exc}")
        return 1

    print(f"Loaded: {getattr(surge, 'descriptive_name', None) or getattr(surge, 'name', None)}")
    if not getattr(surge, "is_instrument", False):
        print("Loaded plugin is not an instrument; MIDI rendering would be invalid.")
        return 1

    try:
        baseline = render_note(
            surge,
            note=60,
            velocity=100,
            note_length=1.25,
            duration=2.0,
            sample_rate=SAMPLE_RATE,
            reset=True,
        )
        summary = assert_render_is_sane(
            baseline,
            SAMPLE_RATE,
            expected_duration=2.0,
            min_dbfs=-60.0,
        )
    except Exception as exc:
        print(f"Render sanity check failed: {type(exc).__name__}: {exc}")
        return 1

    baseline_path = dirs["renders"] / "smoke_surge_c4.wav"
    write_audio(baseline_path, baseline, SAMPLE_RATE)
    print(
        "Baseline render OK: "
        f"shape={summary['shape']}, dbfs={summary['dbfs']:.2f}, peak={summary['peak']:.3f}"
    )
    print(f"Saved {baseline_path}")

    candidate_keys = likely_continuous_parameters(surge, PARAMETER_SEARCH_TERMS)
    if not candidate_keys:
        print("No mutable-looking continuous parameter was found for change verification.")
        return 2

    best_result: tuple[str, float] | None = None
    best_audio = None
    for key in candidate_keys[:40]:
        try:
            changed, difference = try_parameter_change(
                surge,
                baseline,
                key,
                sample_rate=SAMPLE_RATE,
            )
        except Exception as exc:
            print(f"Skipping {key}: {type(exc).__name__}: {exc}")
            continue
        print(f"Parameter trial {key}: mean_abs_difference={difference:.8f}")
        if best_result is None or difference > best_result[1]:
            best_result = (key, difference)
            best_audio = changed
        if difference > 1e-5:
            break

    if best_result is None or best_audio is None:
        print("No candidate parameter could be changed and re-rendered.")
        return 2

    key, difference = best_result
    if difference <= 1e-5:
        print(
            "Parameter changes rendered successfully, but none changed the audio "
            f"measurably. Best={key}, mean_abs_difference={difference:.8f}"
        )
        return 2

    changed_path = dirs["renders"] / f"smoke_surge_c4_changed_{key}.wav"
    write_audio(changed_path, best_audio, SAMPLE_RATE)
    print(
        "Parameter-change render OK: "
        f"key={key}, changed_dbfs={dbfs(best_audio):.2f}, "
        f"mean_abs_difference={mean_absolute_difference(baseline, best_audio):.8f}"
    )
    print(f"Saved {changed_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
