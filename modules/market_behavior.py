"""Price/volume behaviour diagnostics for swing research.

Signals are observable OHLCV proxies only. They cannot identify participants,
prove manipulation, or establish insider trading.
"""
from __future__ import annotations
import math
import pandas as pd


def analyze_price_volume_behavior(frame: pd.DataFrame) -> dict:
    if frame is None or len(frame) < 25:
        return {"label": "CHƯA ĐỦ DỮ LIỆU", "risk_level": "UNKNOWN", "signals": [],
                "cautions": ["Cần ít nhất 25 phiên OHLCV để đánh giá hành vi giá/khối lượng."],
                "metrics": {}}
    x = frame.sort_values("date").tail(60).copy()
    for c in ("open", "high", "low", "close", "volume"):
        x[c] = pd.to_numeric(x[c], errors="coerce")
    x = x.dropna(subset=["open", "high", "low", "close", "volume"])
    if len(x) < 25:
        return {"label": "CHƯA ĐỦ DỮ LIỆU", "risk_level": "UNKNOWN", "signals": [],
                "cautions": ["Dữ liệu OHLCV hợp lệ còn dưới 25 phiên."], "metrics": {}}
    last, prev = x.iloc[-1], x.iloc[-2]
    avg_vol = x.volume.iloc[-21:-1].mean()
    relvol = float(last.volume / avg_vol) if avg_vol and avg_vol > 0 else None
    rng = float(last.high - last.low)
    close_location = float((last.close - last.low) / rng) if rng > 0 else 0.5
    body_pct = float(abs(last.close - last.open) / rng) if rng > 0 else 0.0
    ret = float(last.close / prev.close - 1) if prev.close > 0 else 0.0
    prior_high = float(x.high.iloc[-21:-1].max())
    prior_low = float(x.low.iloc[-21:-1].min())
    signals, cautions = [], []
    risk_points = 0
    # Potential upthrust / bull trap: probes above prior range but closes back inside.
    if last.high > prior_high and last.close < prior_high and relvol is not None and relvol >= 1.3:
        signals.append("Nghi vấn upthrust/bẫy tăng: giá vượt đỉnh 20 phiên trong phiên nhưng đóng cửa trở lại dưới vùng đỉnh, kèm khối lượng cao.")
        risk_points += 2
    # Potential spring / bear trap: probes below prior range but recovers into range.
    if last.low < prior_low and last.close > prior_low and relvol is not None and relvol >= 1.3:
        signals.append("Nghi vấn spring/bẫy giảm: giá xuyên đáy 20 phiên nhưng đóng cửa trở lại phía trên, kèm khối lượng cao.")
    # High volume with little price progress / absorption or distribution ambiguity.
    if relvol is not None and relvol >= 1.8 and abs(ret) <= 0.01:
        signals.append("Khối lượng đột biến nhưng giá tiến triển thấp: có thể là hấp thụ cung/cầu hoặc phân phối; cần xác nhận các phiên sau.")
        risk_points += 1
    # High-volume weak close after an advance: distribution warning proxy.
    if relvol is not None and relvol >= 1.5 and close_location <= 0.25 and ret < 0:
        signals.append("Cảnh báo áp lực bán/phân phối: khối lượng cao, giá đóng cửa gần đáy phiên.")
        risk_points += 2
    # Selling climax / rebound candidate, not a reversal confirmation.
    if relvol is not None and relvol >= 2.0 and ret < -0.025 and close_location >= 0.65:
        signals.append("Có dấu hiệu bán mạnh nhưng được kéo hồi khỏi đáy phiên; có thể là kiệt cung ngắn hạn, chưa đủ xác nhận tạo đáy.")
        risk_points += 1
    # Demand confirmation proxy.
    if relvol is not None and relvol >= 1.5 and ret > 0.015 and close_location >= 0.75:
        signals.append("Cầu chủ động có dấu hiệu xác nhận: tăng giá, khối lượng cao và đóng cửa gần đỉnh phiên.")
    if not signals:
        signals.append("Chưa phát hiện mẫu hình bất thường nổi bật từ OHLCV trong phiên gần nhất.")
    cautions.append("Đây là dấu hiệu hành vi giá/khối lượng, không xác định được danh tính cá mập, giao dịch nội bộ hay hành vi thao túng.")
    cautions.append("Cần dữ liệu sổ lệnh, giao dịch chủ động mua/bán và chuỗi nhiều phiên để tăng độ tin cậy.")
    level = "HIGH" if risk_points >= 3 else "MODERATE" if risk_points >= 1 else "LOW"
    return {"label": "CÓ DẤU HIỆU BẤT THƯỜNG" if risk_points else "CHƯA THẤY BẤT THƯỜNG RÕ",
            "risk_level": level, "signals": signals, "cautions": cautions,
            "metrics": {"relative_volume": relvol, "close_location_in_range": close_location,
                        "return_pct": ret * 100, "prior_20d_high": prior_high,
                        "prior_20d_low": prior_low, "body_pct_of_range": body_pct}}
