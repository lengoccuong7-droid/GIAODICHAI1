import numpy as np
import pandas as pd
from modules.indicators import add_indicators
from modules.swing_trading_expert import analyze_swing_setup, scan_swing_universe


def _uptrend_frame(symbol='AAA', n=260):
    dates = pd.bdate_range('2025-01-01', periods=n)
    close = np.linspace(10000, 15000, n) + np.sin(np.arange(n) / 5) * 80
    volume = np.full(n, 1_000_000.0)
    volume[-1] = 1_500_000
    return pd.DataFrame({
        'date': dates, 'symbol': symbol,
        'open': close - 30, 'high': close + 100,
        'low': close - 100, 'close': close, 'volume': volume,
    })


def test_swing_report_has_5_20_horizon_and_risk_plan():
    enriched = add_indicators(_uptrend_frame())
    report = analyze_swing_setup(
        enriched, market_regime={'regime': 'TĂNG'},
        rs_market={'relative_return_pct': 2.0},
        rs_sector={'relative_return_pct': 1.0},
        documents=[{'filename': 'AAA_Q3.pdf', 'excerpt': 'BCTC Q3'}],
        capital_vnd=100_000_000, risk_pct=1, max_allocation_pct=20,
    )
    assert report['horizon_sessions'] == '5-20'
    assert report['risk_style'] == 'CÂN BẰNG'
    assert report['score'] is not None
    assert report['plan']['reference_trigger'] > report['plan']['invalidation']
    assert report['plan']['target_1'] > report['plan']['reference_trigger']
    assert 'score_is_probability' in report and report['score_is_probability'] is False


def test_swing_position_management_is_separate_from_new_entry():
    enriched = add_indicators(_uptrend_frame())
    report = analyze_swing_setup(
        enriched, market_regime={'regime': 'TĂNG'},
        position={'quantity': 1000, 'entry_price': 12000},
    )
    assert report['position']['mode'] == 'MANAGE_EXISTING'
    assert report['position']['quantity'] == 1000
    assert 'pnl_pct_before_costs' in report['position']


def test_swing_scanner_returns_ranked_dataframe():
    data = pd.concat([_uptrend_frame('AAA'), _uptrend_frame('BBB')], ignore_index=True)
    result = scan_swing_universe(data, market_regime={'regime': 'TĂNG'})
    assert isinstance(result, pd.DataFrame)
    assert set(result['symbol']) == {'AAA', 'BBB'}
    assert result['score'].is_monotonic_decreasing


def test_swing_conflicting_sources_block_new_trade_plan():
    enriched = add_indicators(_uptrend_frame())
    report = analyze_swing_setup(
        enriched, market_regime={'regime': 'TĂNG'},
        rs_market={'relative_return_pct': 2.0},
        rs_sector={'relative_return_pct': 1.0},
        capital_vnd=100_000_000,
        data_conflicts=['Giá từ hai nguồn không đồng nhất'],
        data_quality={'status': 'OK', 'issues': []},
    )
    assert report['status'] != 'TRADE_PLAN_READY'
    assert any('mâu thuẫn' in x.lower() for x in report['blockers'])


def test_swing_plan_is_suppressed_when_no_valid_setup():
    enriched = add_indicators(_uptrend_frame())
    # Force a weak, falling structure with no volume confirmation.
    enriched.loc[enriched.index[-25:], 'close'] = np.linspace(14000, 11000, 25)
    enriched.loc[enriched.index[-25:], 'open'] = enriched.loc[enriched.index[-25:], 'close'] + 50
    enriched.loc[enriched.index[-25:], 'high'] = enriched.loc[enriched.index[-25:], 'open'] + 80
    enriched.loc[enriched.index[-25:], 'low'] = enriched.loc[enriched.index[-25:], 'close'] - 80
    enriched = add_indicators(enriched)
    report = analyze_swing_setup(enriched, market_regime={'regime': 'GIẢM'})
    assert report['status'] in ('STAND_ASIDE', 'WAIT_CONFIRMATION')
    if report['setup'].startswith('BẬT GIÁ') or report['setup'].startswith('KHÔNG CÓ'):
        assert report['plan']['reference_trigger'] is None
        assert report['sizing']['quantity'] == 0


def test_swing_report_integrates_market_behavior_and_valuation():
    enriched = add_indicators(_uptrend_frame())
    report = analyze_swing_setup(
        enriched, market_regime={'regime': 'TĂNG'},
        valuation={'pe': 12.5, 'pb': 1.4},
        fundamental_flags=['CFO chưa được xác minh'],
    )
    assert 'market_behavior' in report
    assert 'valuation' in report
    assert report['valuation']['pe'] == 12.5
    assert report['fundamental_flags'] == ['CFO chưa được xác minh']


def test_existing_position_has_own_targets_and_no_new_entry_sizing():
    enriched = add_indicators(_uptrend_frame())
    report = analyze_swing_setup(
        enriched, market_regime={"regime": "TĂNG"},
        position={"quantity": 500, "entry_price": 12000, "stop_price": 11500},
    )
    pos = report["position"]
    assert pos["mode"] == "MANAGE_EXISTING"
    assert pos["reference_invalidation"] == 11500
    assert pos["target_1_reference"] == 12750
    assert pos["target_2_reference"] == 13000
    assert report["sizing"]["quantity"] == 500
    assert report["sizing"]["status"] == "EXISTING_POSITION_ONLY"


def test_manage_mode_requires_quantity_instead_of_falling_back_to_new_entry():
    enriched = add_indicators(_uptrend_frame())
    report = analyze_swing_setup(
        enriched, position={"mode": "MANAGE_EXISTING", "quantity": 0, "entry_price": 0},
    )
    assert report["position"]["mode"] == "MANAGE_EXISTING"
    assert report["status"] == "POSITION_INPUT_REQUIRED"
    assert report["sizing"]["status"] == "EXISTING_POSITION_ONLY"
    assert any("chưa nhập số lượng" in item.lower() for item in report["blockers"])
