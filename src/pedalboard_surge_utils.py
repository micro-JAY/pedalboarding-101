"""Small utilities for the Pedalboard + Surge XT learning notebook.

The helpers in this module keep the notebook focused on audio concepts rather
than repeated path handling, array-shape checks, and plugin bookkeeping.
"""

from __future__ import annotations

import csv
import importlib.metadata
import math
import os
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
from mido import Message
from pedalboard import AudioUnitPlugin, VST3Plugin, load_plugin
from pedalboard.io import AudioFile


SAMPLE_RATE = 44_100
SILENCE_THRESHOLD_DBFS = -60.0


@dataclass(frozen=True)
class SurgePluginCandidate:
    """A possible Surge XT plugin bundle discovered on disk."""

    path: Path
    plugin_format: str
    plugin_names: tuple[str, ...] = ()
    selected_plugin_name: str | None = None
    scan_error: str | None = None


def project_root() -> Path:
    """Return the repository root from this module's stable location."""

    return Path(__file__).resolve().parents[1]


def ensure_output_dirs(root: Path | None = None) -> dict[str, Path]:
    """Create and return the output directories used by the exercises."""

    root = project_root() if root is None else root
    dirs = {
        "renders": root / "outputs" / "renders",
        "analysis": root / "outputs" / "analysis",
    }
    for directory in dirs.values():
        directory.mkdir(parents=True, exist_ok=True)
    return dirs


def package_version(package_name: str) -> str:
    """Return an installed package version without importing optional packages."""

    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


def ensure_channels_first(audio: np.ndarray | Sequence[float]) -> np.ndarray:
    """Return audio as a float32 array with shape ``(channels, samples)``.

    Pedalboard's file I/O commonly returns channel-first arrays, while many
    plotting and notebook examples start with a one-dimensional mono signal.
    Normalizing the shape once prevents every later exercise from repeating the
    same conditional logic.
    """

    array = np.asarray(audio, dtype=np.float32)
    if array.ndim == 1:
        return array[np.newaxis, :]
    if array.ndim != 2:
        raise ValueError(f"Expected 1D or 2D audio, got shape {array.shape}.")
    if array.shape[0] <= array.shape[1]:
        return array
    return array.T


def to_samples_channels(audio: np.ndarray | Sequence[float]) -> np.ndarray:
    """Return audio in ``(samples, channels)`` form for notebook playback."""

    return ensure_channels_first(audio).T


def mono_mix(audio: np.ndarray | Sequence[float]) -> np.ndarray:
    """Collapse audio to mono for single-trace plots and spectrum checks."""

    channels_first = ensure_channels_first(audio)
    return np.mean(channels_first, axis=0)


def rms(audio: np.ndarray | Sequence[float]) -> float:
    """Return global root-mean-square amplitude."""

    channels_first = ensure_channels_first(audio)
    return float(np.sqrt(np.mean(np.square(channels_first, dtype=np.float64))))


def peak(audio: np.ndarray | Sequence[float]) -> float:
    """Return global absolute peak amplitude."""

    channels_first = ensure_channels_first(audio)
    return float(np.max(np.abs(channels_first))) if channels_first.size else 0.0


def dbfs(audio: np.ndarray | Sequence[float], eps: float = 1e-12) -> float:
    """Return RMS level in dBFS, where a full-scale sine is below 0 dBFS."""

    return float(20.0 * math.log10(max(rms(audio), eps)))


def duration_seconds(audio: np.ndarray | Sequence[float], sample_rate: float) -> float:
    """Return the duration implied by the sample count and sample rate."""

    channels_first = ensure_channels_first(audio)
    return float(channels_first.shape[1] / sample_rate)


def summarize_audio(
    audio: np.ndarray | Sequence[float],
    sample_rate: float,
    *,
    label: str = "audio",
) -> dict[str, float | int | str | tuple[int, ...]]:
    """Return a compact metrics dictionary for lab checks."""

    channels_first = ensure_channels_first(audio)
    return {
        "label": label,
        "shape": tuple(int(value) for value in channels_first.shape),
        "sample_rate": int(sample_rate),
        "duration_seconds": duration_seconds(channels_first, sample_rate),
        "rms": rms(channels_first),
        "dbfs": dbfs(channels_first),
        "peak": peak(channels_first),
    }


def spectral_centroid(audio: np.ndarray | Sequence[float], sample_rate: float) -> float:
    """Estimate spectral centroid in Hz using NumPy's real FFT."""

    mono = mono_mix(audio)
    if mono.size == 0:
        return 0.0
    window = np.hanning(mono.size).astype(np.float32)
    spectrum = np.abs(np.fft.rfft(mono * window))
    magnitude_sum = float(np.sum(spectrum))
    if magnitude_sum <= 0.0:
        return 0.0
    frequencies = np.fft.rfftfreq(mono.size, d=1.0 / sample_rate)
    return float(np.sum(frequencies * spectrum) / magnitude_sum)


def plot_waveform(
    audio: np.ndarray | Sequence[float],
    sample_rate: float,
    title: str,
    seconds: float | None = None,
) -> None:
    """Plot a mono waveform view of the first seconds of audio."""

    import matplotlib.pyplot as plt

    mono = mono_mix(audio)
    max_samples = mono.size if seconds is None else min(mono.size, int(seconds * sample_rate))
    time = np.arange(max_samples) / sample_rate
    plt.figure(figsize=(10, 3))
    plt.plot(time, mono[:max_samples], linewidth=0.9)
    plt.axhline(0, color="black", linewidth=0.5, alpha=0.4)
    plt.title(title)
    plt.xlabel("Time (seconds)")
    plt.ylabel("Amplitude")
    plt.ylim(-1.05, 1.05)
    plt.grid(True, alpha=0.25)
    plt.show()


def plot_spectrum(
    audio: np.ndarray | Sequence[float],
    sample_rate: float,
    title: str,
) -> None:
    """Plot a simple magnitude spectrum for one rendered buffer."""

    import matplotlib.pyplot as plt

    mono = mono_mix(audio)
    if mono.size == 0:
        raise ValueError("Cannot plot the spectrum of an empty audio buffer.")
    window = np.hanning(mono.size).astype(np.float32)
    spectrum = np.abs(np.fft.rfft(mono * window))
    frequencies = np.fft.rfftfreq(mono.size, d=1.0 / sample_rate)
    spectrum_db = 20 * np.log10(np.maximum(spectrum, 1e-9))
    plt.figure(figsize=(10, 3))
    plt.semilogx(frequencies[1:], spectrum_db[1:], linewidth=0.9)
    plt.title(title)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude (dB, relative)")
    plt.grid(True, which="both", alpha=0.25)
    plt.show()


def play_audio(audio: np.ndarray | Sequence[float], sample_rate: float) -> Any:
    """Display playable audio in a Jupyter notebook."""

    from IPython.display import Audio, display

    channels_first = ensure_channels_first(audio)
    data: np.ndarray
    if channels_first.shape[0] == 1:
        data = channels_first[0]
    else:
        data = channels_first
    widget = Audio(data, rate=int(sample_rate), normalize=False)
    display(widget)
    return widget


def write_audio(path: Path, audio: np.ndarray | Sequence[float], sample_rate: float) -> Path:
    """Write channel-first audio to a WAV file."""

    channels_first = ensure_channels_first(audio)
    path.parent.mkdir(parents=True, exist_ok=True)
    with AudioFile(str(path), "w", int(sample_rate), channels_first.shape[0]) as audio_file:
        audio_file.write(channels_first)
    return path


def read_audio(path: Path) -> tuple[np.ndarray, int]:
    """Read an audio file and return ``(audio, sample_rate)``."""

    with AudioFile(str(path)) as audio_file:
        return audio_file.read(audio_file.frames), int(audio_file.samplerate)


def standard_surge_paths() -> list[Path]:
    """Return likely macOS Surge XT plugin paths, including env overrides."""

    paths: list[Path] = []
    override = os.environ.get("SURGE_PLUGIN_PATH")
    if override:
        paths.append(Path(override).expanduser())

    paths.extend(
        [
            Path("/Library/Audio/Plug-Ins/VST3/Surge XT.vst3"),
            Path.home() / "Library/Audio/Plug-Ins/VST3/Surge XT.vst3",
            Path("/Library/Audio/Plug-Ins/Components/Surge XT.component"),
            Path.home() / "Library/Audio/Plug-Ins/Components/Surge XT.component",
        ]
    )

    unique_paths: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.expanduser()
        if resolved not in seen:
            unique_paths.append(resolved)
            seen.add(resolved)
    return unique_paths


def _plugin_format_for_path(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix == ".vst3":
        return "VST3"
    if suffix == ".component":
        return "AudioUnit"
    return None


def _scan_plugin_names(path: Path, plugin_format: str) -> tuple[tuple[str, ...], str | None]:
    scanner = VST3Plugin if plugin_format == "VST3" else AudioUnitPlugin
    try:
        names = tuple(str(name) for name in scanner.get_plugin_names_for_file(str(path)))
    except Exception as exc:
        return (), f"{type(exc).__name__}: {exc}"
    return names, None


def _choose_surge_name(names: Iterable[str]) -> str | None:
    names = tuple(names)
    if not names:
        return None
    instrumentish = [
        name
        for name in names
        if "surge" in name.lower() and "fx" not in name.lower() and "effect" not in name.lower()
    ]
    if instrumentish:
        return instrumentish[0]
    surge_names = [name for name in names if "surge" in name.lower()]
    if surge_names:
        return surge_names[0]
    return names[0] if len(names) == 1 else None


def discover_surge_candidates(scan_plugin_names: bool = True) -> list[SurgePluginCandidate]:
    """Find possible Surge XT plugin bundles and optionally scan plugin names."""

    candidates: list[SurgePluginCandidate] = []
    for path in standard_surge_paths():
        if not path.exists():
            continue
        plugin_format = _plugin_format_for_path(path)
        if plugin_format is None:
            candidates.append(
                SurgePluginCandidate(
                    path=path,
                    plugin_format="unknown",
                    scan_error="Unsupported plugin extension.",
                )
            )
            continue
        names: tuple[str, ...] = ()
        scan_error: str | None = None
        if scan_plugin_names:
            names, scan_error = _scan_plugin_names(path, plugin_format)
        candidates.append(
            SurgePluginCandidate(
                path=path,
                plugin_format=plugin_format,
                plugin_names=names,
                selected_plugin_name=_choose_surge_name(names),
                scan_error=scan_error,
            )
        )
    return candidates


def find_surge_plugin(scan_plugin_names: bool = True) -> SurgePluginCandidate:
    """Return the best discovered Surge XT candidate, preferring VST3."""

    candidates = discover_surge_candidates(scan_plugin_names=scan_plugin_names)
    if not candidates:
        searched = "\n".join(str(path) for path in standard_surge_paths())
        raise FileNotFoundError(f"No Surge XT plugin bundle found. Searched:\n{searched}")

    vst3_candidates = [candidate for candidate in candidates if candidate.plugin_format == "VST3"]
    ordered = vst3_candidates + [candidate for candidate in candidates if candidate.plugin_format != "VST3"]
    return ordered[0]


def load_surge(
    *,
    initialization_timeout: float = 30.0,
    scan_plugin_names: bool = True,
) -> Any:
    """Load Surge XT and require an instrument plugin, not an effect."""

    candidate = find_surge_plugin(scan_plugin_names=scan_plugin_names)
    plugin_name = candidate.selected_plugin_name
    plugin = load_plugin(
        str(candidate.path),
        plugin_name=plugin_name,
        initialization_timeout=initialization_timeout,
    )
    if not getattr(plugin, "is_instrument", False):
        name_hint = f" ({plugin_name})" if plugin_name else ""
        raise RuntimeError(f"Loaded Surge{name_hint}, but it is not an instrument plugin.")
    return plugin


def plugin_metadata(plugin: Any) -> dict[str, Any]:
    """Collect stable identity fields from a Pedalboard external plugin."""

    fields = [
        "name",
        "descriptive_name",
        "manufacturer_name",
        "version",
        "category",
        "is_instrument",
        "is_effect",
    ]
    return {field: getattr(plugin, field, None) for field in fields}


def parameter_table(plugin: Any) -> list[dict[str, Any]]:
    """Return plugin parameters as plain dictionaries for display or CSV."""

    rows: list[dict[str, Any]] = []
    for key, parameter in plugin.parameters.items():
        row = {
            "key": key,
            "display_name": getattr(parameter, "name", None),
            "label": getattr(parameter, "label", None),
            "value": getattr(parameter, "value", None),
            "raw_value": getattr(parameter, "raw_value", None),
        }
        for attr in ["min_value", "max_value", "default_value", "step_count"]:
            row[attr] = getattr(parameter, attr, None)
        rows.append(row)
    return rows


def write_parameter_table_csv(rows: Sequence[dict[str, Any]], path: Path) -> Path:
    """Write a parameter table to CSV using only the standard library."""

    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "key",
        "display_name",
        "label",
        "value",
        "raw_value",
        "min_value",
        "max_value",
        "default_value",
        "step_count",
    ]
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def search_parameters(plugin: Any, *terms: str) -> list[dict[str, Any]]:
    """Search parameter keys, display names, and labels for every term."""

    normalized_terms = [term.lower() for term in terms if term]
    matches: list[dict[str, Any]] = []
    for row in parameter_table(plugin):
        haystack = " ".join(
            str(row.get(field, ""))
            for field in ["key", "display_name", "label", "value"]
        ).lower()
        if all(term in haystack for term in normalized_terms):
            matches.append(row)
    return matches


def print_parameter_matches(plugin: Any, terms: Sequence[str], max_results: int = 30) -> None:
    """Print compact parameter search results for notebook exploration."""

    matches = search_parameters(plugin, *terms)
    if not matches:
        print(f"No matches for {terms!r}.")
        return
    for row in matches[:max_results]:
        print(
            f"{row['key']}: value={row['value']!r}, raw={row['raw_value']!r}, "
            f"name={row['display_name']!r}, label={row['label']!r}"
        )
    if len(matches) > max_results:
        print(f"... {len(matches) - max_results} more matches")


def set_param_if_exists(plugin: Any, key: str, value: Any) -> bool:
    """Set a natural-unit plugin parameter if the normalized key exists."""

    if key not in plugin.parameters:
        warnings.warn(f"Parameter {key!r} was not found; natural-value assignment skipped.")
        return False
    setattr(plugin, key, value)
    return True


def set_raw_param_if_exists(plugin: Any, key: str, raw_value: float) -> bool:
    """Set a normalized raw plugin parameter if the key exists."""

    if not 0.0 <= raw_value <= 1.0:
        raise ValueError(f"raw_value must be in [0, 1], got {raw_value}.")
    if key not in plugin.parameters:
        warnings.warn(f"Parameter {key!r} was not found; raw-value assignment skipped.")
        return False
    plugin.parameters[key].raw_value = float(raw_value)
    return True


def render_note(
    instrument: Any,
    *,
    note: int = 60,
    velocity: int = 100,
    note_length: float = 2.0,
    duration: float = 3.0,
    sample_rate: int = SAMPLE_RATE,
    num_channels: int = 2,
    buffer_size: int = 8192,
    reset: bool = True,
) -> np.ndarray:
    """Render one MIDI note through an instrument plugin."""

    messages = [
        Message("note_on", note=note, velocity=velocity, time=0),
        Message("note_off", note=note, velocity=0, time=note_length),
    ]
    rendered = instrument(
        messages,
        duration=duration,
        sample_rate=sample_rate,
        num_channels=num_channels,
        buffer_size=buffer_size,
        reset=reset,
    )
    return ensure_channels_first(rendered)


def assert_render_is_sane(
    audio: np.ndarray | Sequence[float],
    sample_rate: int,
    *,
    expected_duration: float,
    min_dbfs: float = SILENCE_THRESHOLD_DBFS,
) -> dict[str, Any]:
    """Validate shape, duration, silence threshold, and clipping for a render."""

    summary = summarize_audio(audio, sample_rate)
    if summary["shape"][0] < 1:
        raise AssertionError(f"Expected at least one channel, got {summary['shape']}.")
    if abs(float(summary["duration_seconds"]) - expected_duration) > 0.05:
        raise AssertionError(
            f"Expected about {expected_duration}s, got {summary['duration_seconds']:.3f}s."
        )
    if float(summary["dbfs"]) < min_dbfs:
        raise AssertionError(f"Render is likely silent: {summary['dbfs']:.2f} dBFS.")
    if float(summary["peak"]) > 1.05:
        raise AssertionError(f"Render is clipped above full scale: peak={summary['peak']:.3f}.")
    return summary


def mean_absolute_difference(first: np.ndarray, second: np.ndarray) -> float:
    """Return a length-aligned mean absolute sample difference."""

    a = ensure_channels_first(first)
    b = ensure_channels_first(second)
    channels = min(a.shape[0], b.shape[0])
    samples = min(a.shape[1], b.shape[1])
    if channels == 0 or samples == 0:
        return 0.0
    return float(np.mean(np.abs(a[:channels, :samples] - b[:channels, :samples])))


def likely_continuous_parameters(plugin: Any, terms: Sequence[str] = ()) -> list[str]:
    """Return mutable-looking parameter keys, optionally filtered by search terms."""

    rows = parameter_table(plugin)
    if terms:
        lowered = [term.lower() for term in terms]
        rows = [
            row
            for row in rows
            if any(
                term
                in " ".join(
                    str(row.get(field, ""))
                    for field in ["key", "display_name", "label"]
                ).lower()
                for term in lowered
            )
        ]

    keys: list[str] = []
    for row in rows:
        raw_value = row.get("raw_value")
        value = row.get("value")
        if isinstance(raw_value, (int, float)) and not isinstance(value, str):
            keys.append(str(row["key"]))
    return keys


def try_parameter_change(
    plugin: Any,
    baseline_audio: np.ndarray,
    parameter_key: str,
    *,
    low_raw: float = 0.2,
    high_raw: float = 0.8,
    sample_rate: int = SAMPLE_RATE,
) -> tuple[np.ndarray, float]:
    """Set one raw parameter value, render again, and measure the difference."""

    parameter = plugin.parameters[parameter_key]
    original_raw = getattr(parameter, "raw_value", None)
    if not isinstance(original_raw, (int, float)):
        raise TypeError(f"{parameter_key!r} does not expose a numeric raw_value.")
    target_raw = high_raw if abs(float(original_raw) - high_raw) > 0.1 else low_raw
    try:
        parameter.raw_value = target_raw
        changed_audio = render_note(plugin, sample_rate=sample_rate, reset=True)
    finally:
        parameter.raw_value = float(original_raw)
    return changed_audio, mean_absolute_difference(baseline_audio, changed_audio)


def print_environment_summary() -> None:
    """Print the environment details used by the scripts and notebook."""

    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version.split()[0]}")
    print(f"Current working directory: {Path.cwd()}")
    for package_name in [
        "pedalboard",
        "numpy",
        "matplotlib",
        "mido",
        "jupyter",
        "ipykernel",
        "librosa",
        "pandas",
        "soundfile",
    ]:
        print(f"{package_name}: {package_version(package_name)}")
    override = os.environ.get("SURGE_PLUGIN_PATH")
    print(f"SURGE_PLUGIN_PATH: {override if override else 'not set'}")
