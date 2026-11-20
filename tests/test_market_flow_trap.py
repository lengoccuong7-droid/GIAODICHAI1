import numpy as np
import pandas as pd
from modules.market_flow_trap import analyze_flow_and_traps


def base_frame(n=70):
    close = np.linspace(100, 110, n)
    return pd.DataFrame({
        "date": pd.bdate_range("2026-01-01", periods=n),
        "open": close - 0.2, "high": close + 0.5, "low": close - 0.5,
        "close": close, "volume": np.full(n, 10000.0),
    })


def test_insufficient_data_is_explicit():
    assert analyze_flow_and_traps(base_frame(20))["status"] == "INSUFFICIENT_DATA"


def test_multi_session_bull_trap_is_detected():
    df = base_frame()
    prior_high = df.high.iloc[-21:-1].max()
    i = df.index[-1]
    df.loc[i, ["open", "high", "low", "close", "volume"]] = [prior_high + 1, prior_high + 2, prior_high - 1, prior_high - .5, 30000]
    result = analyze_flow_and_traps(df)
    assert result["metrics"]["bull_trap_events_5"]
    assert result["trap_risk"] == "HIGH"


def test_output_never_claims_known_participant_identity():
    result = analyze_flow_and_traps(base_frame())
    assert any("không xác định" in x.lower() for x in result["cautions"])
    assert "flow_bias" in result
