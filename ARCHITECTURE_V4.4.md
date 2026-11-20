# Architecture V4.4.0 – Flow & Trap Integration

## Data path
`OHLCV -> data validation/enrichment -> analyze_flow_and_traps -> swing decision engine -> Swing UI / Scanner`

## New module
`modules/market_flow_trap.py`
- Validates required OHLCV fields and minimum history.
- Computes CLV-weighted volume proxy, OBV proxy, 20-session relative volume and approximate turnover.
- Scores directional flow only when price/volume proxies align; emits mixed state otherwise.
- Scans recent five sessions against each session's preceding 20-session high/low for potential false breakouts/breakdowns.
- Detects repeated high-volume weak closes as supply/distribution warning proxy.

## Decision integration
- `HIGH` trap risk adds a blocker to new-entry plans.
- Distribution proxy adds a separate blocker.
- The report retains legacy single-session diagnostics while exposing `flow_trap` and nested metrics.
- Scanner carries flow bias and trap risk fields.

## Interpretation constraints
- CLV and OBV are OHLCV-derived proxies, not aggressor-side trade data.
- Approximate turnover uses close × volume and may differ from actual traded value depending on data adjustments.
- Bull trap/spring are hypotheses requiring subsequent-session confirmation.
- No inference about named institutions, insider activity, or manipulation.
- Decision score is a heuristic screening score, not a probability or expected return.
