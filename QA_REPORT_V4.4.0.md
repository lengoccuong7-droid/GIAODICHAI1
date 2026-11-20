# QA Report – V4.4.0

## Automated checks
- `pytest -q`: **40 passed**.
- `python -m compileall -q .`: **passed**.
- Regression suite includes existing V4.3.0 tests plus flow/trap tests for insufficient data, false-breakout detection and participant-identity caveat.

## Not performed
- Streamlit browser/UI runtime test and mobile layout verification.
- Live market-data provider integration test.
- Walk-forward / out-of-sample strategy validation.
- Slippage, fee and tax calibrated portfolio simulation for this new signal layer.

## Release status
Code package is built and automated unit/regression tests pass. Treat as a research/QA build, not a validated investment system. Inspect data quality and verify signals against chart/context before any real-world decision.
