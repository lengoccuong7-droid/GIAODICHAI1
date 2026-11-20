import pandas as pd
import pytest
from modules.shared_analysis import build_shared_analysis_context


def make_frame(symbol="DXG", n=260):
    dates = pd.bdate_range("2024-01-01", periods=n)
    close = pd.Series(range(n), dtype=float) + 10000
    return pd.DataFrame({"date": dates, "symbol": symbol, "open": close-20,
                         "high": close+50, "low": close-50, "close": close,
                         "volume": 1_000_000})


def test_shared_context_has_one_identity_and_core_evidence():
    raw = make_frame()
    result = build_shared_analysis_context("DXG", raw, raw)
    assert result["symbol"] == "DXG"
    assert result["analysis_id"]
    assert result["data_fingerprint"]
    assert "decision_engine" in result
    assert "market_regime" in result
    assert "data_quality" in result


def test_shared_context_rejects_unknown_symbol():
    raw = make_frame()
    with pytest.raises(ValueError, match="Mã cổ phiếu"):
        build_shared_analysis_context("UNKNOWN", raw, raw)


def test_shared_context_rejects_symbol_not_in_uploaded_data():
    raw = make_frame()
    with pytest.raises(ValueError, match="không khớp"):
        build_shared_analysis_context("FPT", raw, raw)
