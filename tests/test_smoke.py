import pandas as pd
from modules.data_loader import normalize_ohlcv
from modules.indicators import add_indicators
from modules.decision_engine import make_trading_decision

def test_pipeline():
    n=260
    dates=pd.bdate_range("2025-01-01",periods=n)
    close=pd.Series([100+i*0.1 for i in range(n)])
    raw=pd.DataFrame({"Date":dates,"Open":close,"High":close+1,"Low":close-1,
                      "Close":close,"Volume":[10000]*n,"Symbol":["TEST"]*n})
    data=normalize_ohlcv(raw)
    enriched=add_indicators(data)
    assert "RSI14" in enriched and "SMA200" in enriched
    decision=make_trading_decision(enriched)
    assert "decision" in decision

import pytest

def test_missing_symbol_requires_explicit_hint():
    raw = pd.DataFrame({
        "Date": pd.date_range("2025-01-01", periods=3),
        "Open": [10, 11, 12], "High": [11, 12, 13],
        "Low": [9, 10, 11], "Close": [10, 11, 12],
        "Volume": [1000, 1100, 1200],
    })
    with pytest.raises(ValueError, match="Không tìm thấy cột mã cổ phiếu"):
        normalize_ohlcv(raw)
    out = normalize_ohlcv(raw, symbol_hint="DXG")
    assert set(out["symbol"]) == {"DXG"}


def test_unknown_or_blank_symbol_requires_hint_or_is_replaced():
    raw = pd.DataFrame({
        "Date": pd.date_range("2025-01-01", periods=3),
        "Symbol": ["DXG", None, "UNKNOWN"],
        "Open": [10, 11, 12], "High": [11, 12, 13],
        "Low": [9, 10, 11], "Close": [10, 11, 12],
        "Volume": [1000, 1100, 1200],
    })
    with pytest.raises(ValueError, match="thiếu mã cổ phiếu"):
        normalize_ohlcv(raw)
    out = normalize_ohlcv(raw, symbol_hint="FPT")
    assert out["symbol"].tolist() == ["DXG", "FPT", "FPT"]
