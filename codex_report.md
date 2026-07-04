# Codex Report

## Documentation and API verification

Documentation was checked with Context7 for `/spotify/pedalboard`, then cross-checked against the installed `tonarpy` runtime.

Verified against Context7 / Pedalboard docs:

- `from pedalboard import Pedalboard, load_plugin`
- `from pedalboard.io import AudioFile`
- `Pedalboard([...])` chains audio effects that process buffers.
- External instrument plugins can render MIDI messages into audio with `duration`, `sample_rate`, `num_channels`, `buffer_size`, and `reset`.
- `plugin.parameters` exposes plugin parameter wrappers.
- Plugin parameters can be set as Python attributes when the normalized key exists.
- `AudioProcessorParameter.raw_value` is normalized on `[0, 1]`.
- `reset=True` clears plugin state before processing; `reset=False` is for continuing chunks from the same stream.
- `VST3Plugin.get_plugin_names_for_file(path)` is available in the local runtime.

Verified by local runtime introspection:

- Python: `3.14.6`
- Pedalboard: `0.9.23`
- `load_plugin(path_to_plugin_file, parameter_values={}, plugin_name=None, initialization_timeout=10.0)`
- `ExternalPlugin.process(midi_messages, duration, sample_rate, num_channels=2, buffer_size=8192, reset=True)`
- `Plugin.process(input_array, sample_rate, buffer_size=8192, reset=True)`
- `LowpassFilter(cutoff_frequency_hz=...)` and `HighpassFilter(cutoff_frequency_hz=...)` instantiate successfully.

## Environment changes

Installed missing required tutorial packages into `tonarpy` only:

- `matplotlib`
- `mido`
- `jupyter`
- `nbconvert`
- `ipykernel`

No global Python packages were installed.

## Surge XT discovery

Found standard macOS plugin candidates:

- `/Library/Audio/Plug-Ins/VST3/Surge XT.vst3`
- `/Library/Audio/Plug-Ins/Components/Surge XT.component`

The VST3 scan reports plugin name `Surge XT`. Loading succeeded as an instrument:

- `name`: `Surge XT`
- `manufacturer_name`: `Surge Synth Team`
- `version`: `1.3.4`
- `category`: `Instrument|Synth`
- `is_instrument`: `True`
- `is_effect`: `True`

Surge prints this warning in the sandbox:

```text
Surge Error [Unable to set up User Directory.]
User directory is non-writable. Operation not permitted: '/Users/minimacro/Documents/Surge XT'
```

Despite the warning, parameter export and audio rendering succeeded. In a normal user-launched Jupyter session, Surge should be able to use its regular user directory.

## Validation results

Passed:

```bash
python scripts/check_env.py
python scripts/list_surge_params.py
python scripts/smoke_test_surge.py
python -m compileall scripts src
jupyter nbconvert --execute notebooks/01_pedalboard_surge_fundamentals.ipynb --to notebook --output 01_pedalboard_surge_fundamentals.executed.ipynb --ExecutePreprocessor.timeout=900
```

Key proof points:

- `scripts/list_surge_params.py` exported 775 Surge parameters to `outputs/analysis/surge_parameters.csv`.
- `scripts/smoke_test_surge.py` rendered MIDI C4 to `outputs/renders/smoke_surge_c4.wav`.
- Smoke-test C4 render measured about `-23.95 dBFS` with peak around `0.212`.
- Smoke test changed `global_volume` and measured a nonzero mean absolute audio difference.
- The final notebook parameter experiment selected `a_filter_1_cutoff` on this Surge XT install.
- Full notebook execution completed and wrote `notebooks/01_pedalboard_surge_fundamentals.executed.ipynb`.
- Agent review flagged optional-`pandas` display fallbacks and cautious repeatability wording; both were fixed, and the notebook was re-executed successfully afterward.

## Notes for future edits

- Keep the notebook focused on the renderer layer. Do not add ML, JUCE, Xcode, or real-time app architecture here.
- Do not hard-code Surge parameter keys as if they are universal. Export and search the parameter table first.
- Treat `raw_value` as the stable dataset-friendly representation and natural units as the human-facing interpretation layer.
- Use `reset=True` for independent dataset renders unless intentionally processing chunks from one continuous stream.
