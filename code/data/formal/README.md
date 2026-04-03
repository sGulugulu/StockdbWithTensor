# Formal Data Placeholder

Put the real A-share production inputs here before running `code/configs/default.yaml`.

Expected files:

- `csi_a500_history.csv`
- `csi_a500_factor_panel.csv`

The formal configuration intentionally points to these paths so that the default run fails fast when real data has not been provided, instead of silently falling back to the bundled smoke-test fixtures.
