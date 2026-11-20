"""Multi-session price/volume flow and price-trap diagnostics.

All outputs are OHLCV-derived proxies. They do not identify market participants,
order aggressors, institutions, or prove manipulation.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

REQUIRED = ("date", "open", "high", "low", "close", "volume")


def _empty(reason: str) -> dict:
    return {
        "status": "INSUFFICIENT_DATA", "flow_label": "CHƯA ĐỦ DỮ LIỆU",
        "flow_score": None, "flow_bias": "UNKNOWN", "trap_risk": "UNKNOWN",
        "trap_label": "CHƯA ĐỦ DỮ LIỆU", "signals": [], "metrics": {},
        "cautions": [reason, "OHLCV không xác định danh tính hoặc ý đồ của người giao dịch."],
    }


def analyze_flow_and_traps(frame: pd.DataFrame, lookback: int = 60) -> dict:
    """Assess multi-session volume/price pressure and false-breakout proxies."""
    if frame is None or len(frame) < 30:
        return _empty("Cần tối thiểu 30 phiên OHLCV hợp lệ; khuyến nghị 60–120 phiên.")
    missing = [c for c in REQUIRED if c not in frame.columns]
    if missing:
        return _empty("Thiếu cột dữ liệu: " + ", ".join(missing))
    x = frame.copy()
    x["date"] = pd.to_datetime(x["date"], errors="coerce")
    for c in REQUIRED[1:]:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    x = x.dropna(subset=list(REQUIRED)).sort_values("date").tail(max(lookback, 30)).reset_index(drop=True)
    x = x[(x.close > 0) & (x.volume >= 0) & (x.high >= x.low) & (x.low > 0)]
    if len(x) < 30:
        return _empty("Sau khi loại dữ liệu lỗi còn dưới 30 phiên hợp lệ.")

    # Close-location value (CLV) is a candle-location proxy, not true bid/ask flow.
    spread = (x.high - x.low).replace(0, np.nan)
    x["clv"] = (((x.close - x.low) - (x.high - x.close)) / spread).fillna(0).clip(-1, 1)
    x["signed_volume_proxy"] = x.clv * x.volume
    x["obv_proxy"] = (np.sign(x.close.diff()).fillna(0) * x.volume).cumsum()
    x["value_proxy"] = x.close * x.volume
    last = x.iloc[-1]
    vol_avg20 = x.volume.iloc[-21:-1].mean()
    rvol = float(last.volume / vol_avg20) if pd.notna(vol_avg20) and vol_avg20 > 0 else None
    flow_5 = float(x.signed_volume_proxy.tail(5).sum())
    flow_20 = float(x.signed_volume_proxy.tail(20).sum())
    flow_scale = float(x.volume.tail(20).sum()) or 1.0
    flow_ratio = flow_20 / flow_scale
    obv_change_20 = float(x.obv_proxy.iloc[-1] - x.obv_proxy.iloc[-21])
    price_change_20 = float(last.close / x.close.iloc[-21] - 1)
    value_avg20 = float(x.value_proxy.iloc[-20:].mean())
    value_last = float(last.value_proxy)

    signals: list[str] = []
    warnings: list[str] = []
    score = 0
    if flow_ratio >= 0.12 and obv_change_20 > 0:
        score += 2
        signals.append("Dòng tiền OHLCV nghiêng về phía cầu trong 20 phiên: CLV-volume và OBV proxy cùng dương.")
    elif flow_ratio <= -0.12 and obv_change_20 < 0:
        score -= 2
        signals.append("Dòng tiền OHLCV nghiêng về phía cung trong 20 phiên: CLV-volume và OBV proxy cùng âm.")
    else:
        signals.append("Dòng tiền OHLCV 20 phiên chưa có hướng đủ rõ hoặc các proxy chưa đồng thuận.")

    if price_change_20 > 0.03 and obv_change_20 <= 0:
        score -= 1
        warnings.append("Phân kỳ tiêu cực: giá tăng nhưng OBV proxy không xác nhận.")
    elif price_change_20 < -0.03 and obv_change_20 > 0:
        score += 1
        signals.append("Phân kỳ tích cực tiềm năng: giá giảm nhưng OBV proxy cải thiện; chưa phải tín hiệu đảo chiều.")

    # Multi-session high-volume weak-close pressure.
    recent = x.tail(5)
    weak_high_vol = 0
    for _, row in recent.iterrows():
        prior = x[x.date < row.date].tail(20)
        avg = prior.volume.mean() if len(prior) else np.nan
        rng = row.high - row.low
        clv = ((row.close - row.low) - (row.high - row.close)) / rng if rng > 0 else 0
        if pd.notna(avg) and avg > 0 and row.volume / avg >= 1.4 and clv <= -0.35:
            weak_high_vol += 1
    if weak_high_vol >= 2:
        score -= 2
        warnings.append(f"Có {weak_high_vol} phiên trong 5 phiên gần nhất: khối lượng cao nhưng đóng cửa yếu; cảnh báo cung/phân phối.")

    # Trap scan: recent 5 sessions against preceding 20-session boundaries.
    bull_traps, bear_traps = [], []
    for i in range(max(20, len(x) - 5), len(x)):
        row = x.iloc[i]
        prior = x.iloc[i-20:i]
        if len(prior) < 20:
            continue
        ph, pl = float(prior.high.max()), float(prior.low.min())
        avg = float(prior.volume.mean())
        rv = float(row.volume / avg) if avg > 0 else 0
        if row.high > ph and row.close < ph and rv >= 1.15:
            bull_traps.append({"date": row.date.strftime("%Y-%m-%d"), "relative_volume": rv, "level": ph})
        if row.low < pl and row.close > pl and rv >= 1.15:
            bear_traps.append({"date": row.date.strftime("%Y-%m-%d"), "relative_volume": rv, "level": pl})
    if bull_traps:
        score -= 2
        warnings.append(f"Nghi vấn {len(bull_traps)} lần false breakout/upthrust trong 5 phiên gần nhất; cần chờ xác nhận tiếp diễn.")
    if bear_traps:
        score += 1
        signals.append(f"Nghi vấn {len(bear_traps)} lần false breakdown/spring; cần xác nhận lực hồi và cấu trúc đáy.")

    # Absorption ambiguity: elevated turnover, narrow progress, closes firm.
    last_range_pct = float((last.high - last.low) / last.close) if last.close else 0
    if rvol is not None and rvol >= 1.7 and last_range_pct <= 0.025 and float(last.clv) >= 0.25:
        signals.append("Có dấu hiệu hấp thụ cung tiềm năng: khối lượng cao, biên độ hẹp và đóng cửa tương đối vững; chưa đủ kết luận tích lũy.")

    bias = "ACCUMULATION_PROXY" if score >= 2 else "DISTRIBUTION_PROXY" if score <= -2 else "MIXED"
    flow_label = {"ACCUMULATION_PROXY": "DÒNG TIỀN NGHIÊNG VỀ CẦU", "DISTRIBUTION_PROXY": "ÁP LỰC CUNG/PHÂN PHỐI", "MIXED": "DÒNG TIỀN CHƯA RÕ"}[bias]
    trap_risk = "HIGH" if bull_traps or weak_high_vol >= 2 else "MODERATE" if bear_traps or warnings else "LOW"
    trap_label = {"HIGH": "RỦI RO BẪY TĂNG/PHÂN PHỐI CAO", "MODERATE": "CÓ DẤU HIỆU CẦN XÁC MINH", "LOW": "CHƯA THẤY BẪY GIÁ RÕ"}[trap_risk]
    if not signals:
        signals.append("Chưa có tín hiệu dòng tiền nổi bật theo các proxy đang sử dụng.")
    cautions = [
        "Dòng tiền lớn chỉ được suy luận gián tiếp từ OHLCV; không xác định được danh tính tổ chức hay cá nhân mua/bán.",
        "Không có dữ liệu sổ lệnh hoặc bên chủ động khớp lệnh nên không thể xác nhận dòng tiền tổ chức.",
        "Upthrust/spring là mẫu hình nghi vấn; cần 1–3 phiên sau xác nhận, không coi một phiên là bằng chứng thao túng.",
        "Giá trị giao dịch xấp xỉ = giá đóng cửa × khối lượng, không thay thế giá trị khớp lệnh thực tế nếu dữ liệu đã điều chỉnh.",
    ]
    return {
        "status": "OK", "flow_label": flow_label, "flow_score": int(score),
        "flow_bias": bias, "trap_risk": trap_risk, "trap_label": trap_label,
        "signals": signals + warnings, "warnings": warnings,
        "metrics": {
            "relative_volume_20": rvol, "flow_ratio_20": flow_ratio,
            "flow_proxy_5": flow_5, "flow_proxy_20": flow_20,
            "obv_proxy_change_20": obv_change_20, "price_change_20_pct": price_change_20 * 100,
            "average_value_proxy_20": value_avg20, "latest_value_proxy": value_last,
            "weak_high_volume_sessions_5": weak_high_vol,
            "bull_trap_events_5": bull_traps, "bear_trap_events_5": bear_traps,
        }, "cautions": cautions,
    }
