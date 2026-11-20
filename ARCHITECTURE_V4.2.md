# BOT TRADER SWING MULTI V4.2.1 — Architecture

## Product objective
Deliver one clear, explainable 5–20-session Swing Trading decision brief. The app is a decision-support/research tool, not an order executor or a guaranteed-return predictor.

## Shared data path
`data_loader.normalize_ohlcv` (strict symbol validation; never invent UNKNOWN) -> explicit `price_units.normalize_price_unit` -> `data_quality.assess_data_quality` and `audit_flags` -> `indicators.add_indicators` -> market/relative-strength/multi-timeframe/fundamental modules -> `swing_trading_expert.analyze_swing_setup` -> one Swing decision and plan.

All price calculations use VND/share after explicit user-selected normalization. Volume remains shares. The Swing expert is the single source of truth for its entry zone, invalidation and targets; Dashboard is descriptive and does not issue a second plan.

## Reasoning components
- Technical trend/momentum/volatility and 20-session structure.
- Bounce vs early recovery vs confirmed recovery classification.
- Price/volume anomaly proxies: upthrust, spring, high-volume low-progress, weak-close distribution warning, potential selling climax, and demand confirmation.
- Fundamental valuation ratios only when supplied inputs are valid; no rich/cheap conclusion without same-period peer/history comparison.
- Market regime, relative strength, data-quality warnings, user position and risk sizing. New-entry sizing is isolated from existing-position valuation; the manage-existing path reports its own reference invalidation and risk-multiple targets.
- Contradictions and missing evidence are shown as blockers/reasons, not silently resolved.

## Interpretation limits
OHLCV proxies cannot identify a market participant, prove manipulation, or establish insider trading. No order-book/transaction-level inference is claimed unless those data are actually supplied. Heuristic score is not win probability. The rules require out-of-sample/walk-forward validation before operational use.

## File integration
`app.py` imports each module by package path under `modules/`. `modules/__init__.py` is retained. Tests exercise the key module interfaces and the import graph. Keep module names stable; shared schemas are passed as dictionaries/dataframes with explicit field names.
