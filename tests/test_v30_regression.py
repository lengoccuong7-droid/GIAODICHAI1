import numpy as np
import pandas as pd
from modules.indicators import add_indicators
from modules.risk_manager import calculate_position_size
from modules.relative_strength import relative_strength
from modules.multi_timeframe import resample_ohlcv, timeframe_snapshot
from modules.fundamental_analysis import valuation_metrics, quality_flags
from modules.backtest import simple_swing_backtest
from modules.market_analysis import analyze_universe
from modules.stock_scanner import scan_universe
from modules.price_units import normalize_price_unit
from modules.data_loader import normalize_ohlcv


def sample_frame(symbol='AAA', n=320, base=20.0):
    dates = pd.bdate_range('2024-01-01', periods=n)
    close = base + np.arange(n) * 0.03 + np.sin(np.arange(n) / 7) * 0.4
    return pd.DataFrame({'date': dates, 'symbol': symbol, 'open': close-.1,
        'high': close+.5, 'low': close-.5, 'close': close, 'volume': 100000 + np.arange(n)*100})


def test_supertrend_initializes_after_atr_warmup():
    out = add_indicators(sample_frame())
    assert out['SUPERTREND10_3'].notna().sum() > 250
    assert set(out['SUPERTREND_DIRECTION'].dropna().unique()).issubset({-1.0, 1.0})


def test_position_size_normalizes_thousand_vnd_price():
    # Source price 25 means 25,000 VND; risk sizing is calculated in VND.
    out = calculate_position_size(100_000_000, 25, 23, 1, 20, 100, 1000)
    assert out['quantity'] == 500
    assert out['position_value'] == 12_500_000
    assert out['risk_amount'] == 1_000_000


def test_relative_strength_aligns_common_dates():
    stock = sample_frame('AAA', 80)
    bench = sample_frame('VNINDEX', 75, 100)
    result = relative_strength(stock, bench, 20)
    assert result['return_pct'] is not None
    assert result['relative_return_pct'] is not None


def test_weekly_monthly_resampling():
    frame = sample_frame()
    weekly = resample_ohlcv(frame, 'W-FRI')
    snap = timeframe_snapshot(frame)
    assert len(weekly) < len(frame)
    assert snap['W']['bars'] > 40
    assert snap['M']['bars'] > 10


def test_fundamental_metrics_and_quality_flags():
    vals = valuation_metrics(price_vnd=30000, eps_vnd=3000, bvps_vnd=15000)
    assert vals['pe'] == 10
    assert vals['pb'] == 2
    ev = valuation_metrics(price_vnd=30000, eps_vnd=3000, bvps_vnd=15000, net_debt=-1_000_000, ebitda=500_000, market_cap=10_000_000)
    assert ev['ev_ebitda'] == 18
    assert valuation_metrics(price_vnd=30000, eps_vnd=3000, bvps_vnd=15000, ebitda=500_000, market_cap=10_000_000)['ev_ebitda'] is None
    flags = quality_flags(revenue_growth=20, profit_growth=5, roe=10, cfo=-1, net_profit=10, debt_to_equity=250)
    assert len(flags) >= 3


def test_scanner_is_connected_and_ranks_universe():
    data = pd.concat([sample_frame('AAA'), sample_frame('BBB', base=30)], ignore_index=True)
    universe = analyze_universe(data)
    scanned = scan_universe(universe, data)
    assert len(scanned) == 2
    assert 'Điểm tổng (heuristic)' in scanned.columns


def test_backtest_tax_is_applied_and_reported():
    n = 220
    close = np.r_[np.linspace(20, 40, 140), np.linspace(40, 20, 80)]
    frame = pd.DataFrame({'date': pd.bdate_range('2024-01-01', periods=n), 'symbol': 'AAA',
        'open': close, 'high': close*1.01, 'low': close*.99, 'close': close, 'volume': 100000})
    no_tax = simple_swing_backtest(frame, fee_pct=0, slippage_pct=0, tax_pct=0, initial_capital=100_000_000)
    with_tax = simple_swing_backtest(frame, fee_pct=0, slippage_pct=0, tax_pct=.1, initial_capital=100_000_000)
    assert no_tax['closed_trades'] > 0
    assert with_tax['assumptions']['tax_pct_exit'] == .1
    assert no_tax['final_equity'] > with_tax['final_equity']


def test_price_unit_conversion_changes_ohlc_not_volume():
    raw = sample_frame(n=3)
    out = normalize_price_unit(raw, 1000)
    assert out.close.iloc[0] == raw.close.iloc[0] * 1000
    assert out.volume.equals(raw.volume)
    assert out.attrs["price_unit"] == "VND/share"


def test_loader_parses_iso_and_vietnamese_dates_without_day_month_swap():
    iso = pd.DataFrame({'Date':['2024-01-02','2024-02-05'], 'Symbol':['AAA','AAA'],
        'Open':[10,11], 'High':[12,13], 'Low':[9,10], 'Close':[11,12], 'Volume':[100,120]})
    out = normalize_ohlcv(iso)
    assert out.date.iloc[0] == pd.Timestamp('2024-01-02')
    assert out.date.iloc[1] == pd.Timestamp('2024-02-05')
    vn = iso.copy(); vn['Date']=['02/01/2024','05/02/2024']
    out_vn = normalize_ohlcv(vn)
    assert out_vn.date.iloc[0] == pd.Timestamp('2024-01-02')
    assert out_vn.date.iloc[1] == pd.Timestamp('2024-02-05')
