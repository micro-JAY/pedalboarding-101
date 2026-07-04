# Pedalboarding 101

A hands-on learning repo for using [Spotify Pedalboard](https://github.com/spotify/pedalboard) with Surge XT as a software synth plugin.

This project is a practical tutorial for learning how Python can act like a lightweight audio plugin host: load a synth, send MIDI, render audio, inspect parameters, process audio with effects, and save the results for later analysis.

The repo is intentionally small and educational. It is not a production audio engine, DAW, ML pipeline, or plugin development project.

## Start Here

Activate the audio environment, then open the notebook:

```bash
tonarpy
jupyter lab notebooks/01_pedalboard_surge_fundamentals.ipynb
```

The notebook is the primary learning artifact. It is written like a lab manual: each section starts from a concrete problem, introduces only the API needed to solve that problem, then checks the result with shapes, metrics, plots, saved files, or audio playback.

## Goals

This repo teaches the fundamentals of programmatic audio rendering:

- Representing audio as NumPy arrays
- Understanding sample rate, frames, channels, RMS, peak, and dBFS
- Using Pedalboard built-in effects
- Loading Surge XT as a VST3 or Audio Unit plugin
- Sending MIDI notes to a synth plugin
- Rendering audio from MIDI
- Inspecting plugin parameters
- Setting plugin parameters safely
- Saving rendered WAV files
- Creating small metadata tables for experiments
- Building intuition for future audio dataset generation

## What This Is Not

This repo does **not** cover:

- JUCE
- Xcode
- CoreML
- ML model training
- Plugin development
- Real-time app development
- Full PatchPilot / PPv2 architecture
- Large-scale dataset generation

Those are later-stage topics. This repo focuses on the renderer layer: **parameters + MIDI in, audio out**.

## Project Layout

```text
.
├── notebooks/
│   └── 01_pedalboard_surge_fundamentals.ipynb
├── scripts/
│   ├── check_env.py
│   ├── list_surge_params.py
│   └── smoke_test_surge.py
├── src/
│   └── pedalboard_surge_utils.py
├── outputs/
│   ├── renders/
│   └── analysis/
├── NOTEBOOK_CHECKS.md
└── codex_report.md
```

## Verification

Run the lightweight checks first:

```bash
tonarpy
python scripts/check_env.py
python -m compileall scripts src
```

Then run the Surge-specific checks:

```bash
python scripts/list_surge_params.py
python scripts/smoke_test_surge.py
```

The full notebook execution command is recorded in `NOTEBOOK_CHECKS.md`.

## Surge XT Path

The helpers check `SURGE_PLUGIN_PATH` first, then the standard macOS locations:

- `/Library/Audio/Plug-Ins/VST3/Surge XT.vst3`
- `~/Library/Audio/Plug-Ins/VST3/Surge XT.vst3`
- `/Library/Audio/Plug-Ins/Components/Surge XT.component`
- `~/Library/Audio/Plug-Ins/Components/Surge XT.component`

Prefer the VST3 instrument when both VST3 and Audio Unit versions are installed.
