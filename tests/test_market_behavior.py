import numpy as np
import pandas as pd
from modules.market_behavior import analyze_price_volume_behavior


def _frame(n=40):
    close = np.linspace(100, 110, n)
    return pd.DataFrame({
        'date': pd.bdate_range('2026-01-01', periods=n),
        'open': close - .3, 'high': close + .5, 'low': close - .5,
        'close': close, 'volume': np.full(n, 1000.0),
    })


def test_behavior_insufficient_data_is_explicit():
    result = analyze_price_volume_behavior(_frame(10))
    assert result['risk_level'] == 'UNKNOWN'
    assert result['label'] == 'CHƯA ĐỦ DỮ LIỆU'


def test_behavior_flags_high_volume_upthrust_without_claiming_identity():
    frame = _frame()
    prior_high = frame.high.iloc[-21:-1].max()
    frame.loc[frame.index[-1], 'high'] = prior_high + 2
    frame.loc[frame.index[-1], 'open'] = prior_high + 0.5
    frame.loc[frame.index[-1], 'close'] = prior_high - 0.5
    frame.loc[frame.index[-1], 'low'] = prior_high - 1
    frame.loc[frame.index[-1], 'volume'] = 3000
    result = analyze_price_volume_behavior(frame)
    assert any('upthrust' in x.lower() for x in result['signals'])
    assert any('không xác định' in x.lower() for x in result['cautions'])
