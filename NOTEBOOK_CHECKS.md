# Notebook Checks

Use these checks after editing the notebook or utility module.

## Quick checks

```bash
tonarpy
python scripts/check_env.py
python -m compileall scripts src
```

## Surge checks

These require Surge XT to load successfully in the active environment:

```bash
tonarpy
python scripts/list_surge_params.py
python scripts/smoke_test_surge.py
```

## Full notebook execution

```bash
tonarpy
jupyter nbconvert --execute notebooks/01_pedalboard_surge_fundamentals.ipynb \
  --to notebook \
  --output 01_pedalboard_surge_fundamentals.executed.ipynb \
  --ExecutePreprocessor.timeout=900
```

If the notebook fails at Surge loading, first run `scripts/check_env.py` and
confirm `SURGE_PLUGIN_PATH` or the standard macOS plugin paths.
