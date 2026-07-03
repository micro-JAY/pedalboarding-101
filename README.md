# Pedalboarding 101

A hands-on learning repo for using [Spotify Pedalboard](https://github.com/spotify/pedalboard) with Surge XT as a software synth plugin.

This project is a practical tutorial for learning how Python can act like a lightweight audio plugin host: load a synth, send MIDI, render audio, inspect parameters, process audio with effects, and save the results for later analysis.

The repo is intentionally small and educational. It is not a production audio engine, DAW, ML pipeline, or plugin development project.

---

## Goals

This repo is for learning the fundamentals of programmatic audio rendering:

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

---

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

---

## Why Pedalboard?

Pedalboard is a Python audio processing library from Spotify. It can process audio with built-in effects and host third-party plugins such as VST3 and Audio Units.

For this repo, the important idea is:

```text
Python script
   ↓
Pedalboard loads Surge XT
   ↓
Python sends MIDI notes
   ↓
Surge XT renders audio
   ↓
Pedalboard / NumPy analyze or process the result
   ↓
WAV files and metadata are saved
