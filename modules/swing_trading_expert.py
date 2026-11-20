"""Swing Trading Expert for 5-20 sessions.

Deterministic, explainable research engine. It does not predict prices or execute orders.
All thresholds are transparent heuristics and must be validated with out-of-sample tests.
"""
from __future__ import annotations
from typing import Any
import math
import pandas as pd
from .indicators import add_indicators
from .risk_manager import calculate_position_size
from .market_behavior import analyze_price_volume_behavior
from .market_flow_trap import analyze_flow_and_traps

HORIZON_SESSIONS = (5, 20)
DEFAULT_STYLE = "CÂN BẰNG"


def _num(value: Any) -> float | None:
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def _market_gate(regime: dict | None) -> tuple[str, list[str]]:
    regime = regime or {}
    name = str(regime.get("regime", "CHƯA CÓ DỮ LIỆU")).upper()
    reasons = list(regime.get("reasons", []) or [])
    if any(x in name for x in ("GIẢM", "BEAR", "DOWN")):
        return "DEFENSIVE", ["Thị trường chung bất lợi: hạ mức quyết liệt, yêu cầu xác nhận mạnh hơn."] + reasons
    if any(x in name for x in ("TĂNG", "BULL", "UP")):
        return "SUPPORTIVE", ["Thị trường chung tương đối thuận lợi cho chiến lược theo xu hướng."] + reasons
    return "NEUTRAL", ["Thị trường chung chưa xác nhận xu hướng thuận lợi rõ ràng."] + reasons


def analyze_swing_setup(enriched: pd.DataFrame, market_regime: dict | None = None,
                        rs_market: dict | None = None, rs_sector: dict | None = None,
                        documents: list[dict] | None = None,
                        capital_vnd: float = 100_000_000, risk_pct: float = 1.0,
                        max_allocation_pct: float = 20.0, lot_size: int = 100,
                        position: dict | None = None, risk_style: str = DEFAULT_STYLE,
                        data_conflicts: list[str] | None = None,
                        data_quality: dict | None = None,
                        valuation: dict | None = None, fundamental_flags: list[str] | None = None) -> dict:
    """Explainable 5-20 session decision engine. All prices are assumed VND/share."""
    position = position or {}
    documents = documents or []
    data_conflicts = data_conflicts or []
    valuation = valuation or {}
    fundamental_flags = fundamental_flags or []
    data_quality = data_quality or {"status": "UNKNOWN", "issues": []}
    if enriched is None or len(enriched) < 50:
        return {"status": "INSUFFICIENT_DATA", "decision": "ĐỨNG NGOÀI – THIẾU DỮ LIỆU",
                "symbol": None, "horizon_sessions": "5-20", "setup": "CHƯA ĐỦ DỮ LIỆU",
                "score": None, "reasons": ["Cần tối thiểu 50 phiên OHLCV hợp lệ."],
                "blockers": ["Thiếu lịch sử giá tối thiểu"], "documents": documents}

    x = enriched.sort_values("date").reset_index(drop=True).copy()
    last, prev = x.iloc[-1], x.iloc[-2]
    symbol_value = last.get("symbol")
    symbol = str(symbol_value).strip().upper() if symbol_value is not None and not pd.isna(symbol_value) else ""
    if not symbol or symbol in {"UNKNOWN", "NONE", "NAN"}:
        return {"status": "INSUFFICIENT_DATA", "decision": "ĐỨNG NGOÀI – CHƯA XÁC ĐỊNH MÃ",
                "symbol": None, "horizon_sessions": "5-20", "setup": "CHƯA ĐỦ DỮ LIỆU",
                "score": None, "reasons": ["Không có mã cổ phiếu hợp lệ trong dữ liệu."],
                "blockers": ["Chặn phân tích khi thiếu mã; không tự gán UNKNOWN."], "documents": documents}
    close, high, low = _num(last.get("close")), _num(last.get("high")), _num(last.get("low"))
    ma5, ma20, ma50 = _num(last.get("SMA5")), _num(last.get("SMA20")), _num(last.get("SMA50"))
    prev_ma20 = _num(x.iloc[-6].get("SMA20")) if len(x) >= 6 else None
    prev_close = _num(prev.get("close"))
    rsi, atr = _num(last.get("RSI14")), _num(last.get("ATR14"))
    relvol, adx = _num(last.get("REL_VOLUME20")), _num(last.get("ADX14"))
    macdh = _num(last.get("MACD_HIST"))
    needed = {"close": close, "high": high, "low": low, "SMA20": ma20,
              "SMA50": ma50, "RSI14": rsi, "ATR14": atr,
              "REL_VOLUME20": relvol, "MACD_HIST": macdh}
    missing = [k for k, v in needed.items() if v is None]
    if missing or close is None or close <= 0 or atr is None or atr <= 0:
        return {"status": "INSUFFICIENT_DATA", "decision": "ĐỨNG NGOÀI – DỮ LIỆU KHÔNG HỢP LỆ",
                "symbol": symbol, "horizon_sessions": "5-20", "setup": "CHƯA ĐỦ DỮ LIỆU",
                "score": None, "reasons": ["Thiếu hoặc sai chỉ báo: " + ", ".join(missing)],
                "blockers": ["Không lập kế hoạch giá khi dữ liệu đầu vào chưa hợp lệ"], "documents": documents}

    positives, negatives, reasons, blockers = [], [], [], []
    # Unified multi-session flow/trap assessment. Legacy single-session diagnostics
    # are retained as supplementary context, not as the sole decision input.
    flow_trap = analyze_flow_and_traps(x)
    legacy_behavior = analyze_price_volume_behavior(x)
    behavior = {
        **legacy_behavior,
        "flow_trap": flow_trap,
        "flow_label": flow_trap.get("flow_label"),
        "flow_bias": flow_trap.get("flow_bias"),
        "trap_label": flow_trap.get("trap_label"),
        "trap_risk": flow_trap.get("trap_risk"),
        "flow_metrics": flow_trap.get("metrics", {}),
        "signals": list(dict.fromkeys(legacy_behavior.get("signals", []) + flow_trap.get("signals", []))),
        "cautions": list(dict.fromkeys(legacy_behavior.get("cautions", []) + flow_trap.get("cautions", []))),
    }
    if flow_trap.get("trap_risk") == "HIGH":
        blockers.append("Rủi ro bẫy tăng/phân phối cao theo nhiều phiên OHLCV; chờ xác nhận, không kích hoạt điểm vào mới.")
    if flow_trap.get("flow_bias") == "DISTRIBUTION_PROXY":
        blockers.append("Proxy dòng tiền 20 phiên nghiêng về phía cung/phân phối; yêu cầu xác nhận lại trước khi mở vị thế.")
    if behavior.get("risk_level") == "HIGH":
        blockers.append("Phát hiện dấu hiệu hành vi giá/khối lượng rủi ro cao; chờ xác nhận thêm.")
    elif behavior.get("risk_level") == "MODERATE":
        reasons.append("Có dấu hiệu hành vi giá/khối lượng cần theo dõi; không kết luận có thao túng.")
    score = 0
    trend_up = close > ma20 > ma50
    trend_down = close < ma20 < ma50
    ma20_rising = prev_ma20 is not None and ma20 > prev_ma20
    price_rising = prev_close is not None and close > prev_close

    if trend_up:
        score += 20; positives.append("Xu hướng tăng đồng thuận: giá > MA20 > MA50.")
    elif trend_down:
        score -= 25; negatives.append("Xu hướng giảm đồng thuận: giá < MA20 < MA50.")
    else:
        reasons.append("Xu hướng chưa đồng thuận giữa giá, MA20 và MA50.")

    if 50 <= rsi <= 68:
        score += 12; positives.append(f"RSI14={rsi:.1f}: động lượng tích cực, chưa quá nóng theo ngưỡng tham chiếu.")
    elif rsi > 75:
        score -= 8; negatives.append(f"RSI14={rsi:.1f}: rủi ro mua đuổi cao.")
    elif rsi < 40:
        score -= 8; negatives.append(f"RSI14={rsi:.1f}: động lượng yếu; chưa thể coi là tín hiệu tạo đáy.")
    else:
        score += 3; reasons.append(f"RSI14={rsi:.1f}: động lượng trung tính.")

    if relvol >= 1.3:
        score += 15; positives.append(f"Relative Volume={relvol:.2f}x: dòng tiền/khối lượng xác nhận tương đối tốt.")
    elif relvol >= 1.0:
        score += 7; positives.append(f"Relative Volume={relvol:.2f}x: khối lượng đạt trung bình.")
    else:
        score -= 8; negatives.append(f"Relative Volume={relvol:.2f}x: thanh khoản chưa xác nhận.")
    if macdh >= 0:
        score += 8; positives.append("MACD Histogram không âm.")
    else:
        score -= 6; negatives.append("MACD Histogram âm.")
    if adx is not None and adx >= 25:
        score += 6; positives.append(f"ADX14={adx:.1f}: xu hướng có cường độ tương đối rõ.")

    prior = x.iloc[-21:-1]
    prior_high = _num(prior.high.max()) if len(prior) == 20 else None
    prior_low = _num(prior.low.min()) if len(prior) == 20 else None
    recent_low = _num(x.low.tail(20).min())
    recent_high = _num(x.high.tail(20).max())
    breakout = prior_high is not None and close > prior_high and relvol >= 1.3
    pullback = trend_up and abs(close - ma20) <= 0.75 * atr and rsi >= 45
    base_range_pct = ((prior_high - prior_low) / prior_low * 100) if prior_high and prior_low and prior_low > 0 else None
    base = base_range_pct is not None and base_range_pct <= 12 and close >= ma20

    # Separate a technical bounce from a genuine trend recovery.
    recovery_confirmed = (not trend_up and ma20_rising and close > ma20 and
                          (ma5 is None or close > ma5) and rsi >= 50 and macdh >= 0 and relvol >= 1.1)
    early_recovery = (not trend_up and close > ma20 and ma20_rising and price_rising)
    bounce_pct = ((close / recent_low) - 1) * 100 if recent_low and recent_low > 0 else 0
    technical_bounce = (price_rising and bounce_pct >= 3.0 and not recovery_confirmed and
                        (close < ma20 or trend_down))

    if breakout:
        setup = "BREAKOUT XÁC NHẬN"
        score += 15
        positives.append(f"Đóng cửa vượt đỉnh 20 phiên trước; Relative Volume={relvol:.2f}x.")
    elif pullback:
        setup = "PULLBACK TRONG XU HƯỚNG TĂNG"
        score += 12
        positives.append("Giá điều chỉnh về gần MA20 trong xu hướng tăng; chờ nến xác nhận bật lên.")
    elif recovery_confirmed:
        setup = "HỒI PHỤC CÓ XÁC NHẬN"
        score += 12
        positives.append("Giá vượt MA20, MA20 cải thiện, RSI/MACD và khối lượng cùng xác nhận hồi phục.")
    elif early_recovery:
        setup = "HỒI PHỤC SỚM – CHƯA XÁC NHẬN"
        score += 4
        reasons.append("Giá đã vượt MA20 và MA20 cải thiện nhưng động lượng/khối lượng chưa xác nhận đầy đủ.")
    elif technical_bounce:
        setup = "BẬT GIÁ KỸ THUẬT – CHƯA PHẢI ĐẢO CHIỀU"
        score -= 5
        negatives.append(f"Giá hồi {bounce_pct:.1f}% từ đáy 20 phiên nhưng cấu trúc xu hướng chưa xác nhận đảo chiều.")
    elif base:
        setup = "NỀN TÍCH LŨY"
        score += 7
        positives.append(f"Biên độ nền 20 phiên khoảng {base_range_pct:.1f}%; chưa có breakout xác nhận.")
    else:
        setup = "KHÔNG CÓ MẪU HÌNH SWING ĐẠT CHUẨN"
        reasons.append("Chưa đạt tiêu chí breakout, pullback, hồi phục hoặc nền tích lũy.")

    gate, gate_reasons = _market_gate(market_regime)
    reasons.extend(gate_reasons)
    if data_conflicts:
        blockers.append("Còn mâu thuẫn giữa các nguồn dữ liệu: cần giải quyết trước khi giao dịch")
        reasons.extend(["Mâu thuẫn: " + str(v) for v in data_conflicts[:5]])
    quality_status = str(data_quality.get("status", "UNKNOWN")).upper()
    if quality_status == "ERROR":
        blockers.append("Chất lượng dữ liệu OHLCV ở trạng thái ERROR")
    elif quality_status == "WARNING":
        blockers.append("Dữ liệu có cảnh báo độ trễ; cần cập nhật trước khi kích hoạt giao dịch")
    if gate == "SUPPORTIVE": score += 8
    elif gate == "DEFENSIVE": score -= 15; blockers.append("Thị trường chung đang ở trạng thái phòng thủ")

    for label, rs in (("VN-Index", rs_market or {}), ("ngành", rs_sector or {})):
        rel = _num(rs.get("relative_return_pct"))
        if rel is None:
            reasons.append(f"Chưa có dữ liệu RS đồng bộ so với {label}.")
        elif rel > 0:
            score += 5; positives.append(f"Sức mạnh tương đối vượt {label} ({rel:+.2f}%).")
        else:
            score -= 5; negatives.append(f"Sức mạnh tương đối yếu hơn {label} ({rel:+.2f}%).")

    # One coherent plan is generated only for actionable setups.
    if setup == "BREAKOUT XÁC NHẬN":
        trigger = prior_high + 0.05 * atr
    elif setup == "PULLBACK TRONG XU HƯỚNG TĂNG":
        trigger = max(ma20, close) + 0.05 * atr
    elif setup == "HỒI PHỤC CÓ XÁC NHẬN":
        trigger = max(high, close) + 0.05 * atr
    elif setup == "NỀN TÍCH LŨY":
        trigger = prior_high + 0.05 * atr
    else:
        trigger = None

    recent_support = _num(x.low.tail(10).min())
    stop = max(0.01, min(recent_support, (trigger - 1.5 * atr)) if trigger is not None and recent_support is not None else (trigger - 1.5 * atr) if trigger is not None else close - 1.5 * atr)
    target_1 = trigger + 1.5 * (trigger - stop) if trigger is not None and trigger > stop else None
    target_2 = trigger + 2.0 * (trigger - stop) if trigger is not None and trigger > stop else None
    rr_1 = (target_1-trigger)/(trigger-stop) if target_1 is not None and trigger > stop else None
    rr_2 = (target_2-trigger)/(trigger-stop) if target_2 is not None and trigger > stop else None

    if trend_down:
        blockers.append("Xu hướng giảm chưa bị phá vỡ")
    if setup in ("BẬT GIÁ KỸ THUẬT – CHƯA PHẢI ĐẢO CHIỀU", "HỒI PHỤC SỚM – CHƯA XÁC NHẬN", "KHÔNG CÓ MẪU HÌNH SWING ĐẠT CHUẨN"):
        blockers.append("Chưa có mô hình giao dịch được xác nhận")
    if relvol < 1.1:
        blockers.append("Khối lượng chưa đạt ngưỡng xác nhận 1.1x")
    if trigger is not None and close > trigger + 0.75 * atr:
        blockers.append("Giá đã chạy xa vùng kích hoạt; không đuổi giá")
    if behavior.get("risk_level") == "HIGH":
        blockers.append("Dấu hiệu bẫy giá/phân phối cần được xác minh qua các phiên tiếp theo")
    if rr_1 is not None and rr_1 < 1.5:
        blockers.append("R:R mục tiêu 1 chưa đạt 1.5R")

    if risk_style.upper().startswith("THẬN"):
        min_score = 70
    elif "CAO" in risk_style.upper() or "AGGRESSIVE" in risk_style.upper():
        min_score = 55
    else:
        min_score = 65
    score = max(0, min(100, int(score)))
    if score < min_score:
        blockers.append(f"Điểm Swing {score}/100 thấp hơn ngưỡng cân bằng {min_score}/100")

    sizing = calculate_position_size(capital_vnd, trigger or close, stop, risk_pct,
                                     max_allocation_pct, lot_size, 1.0)
    if trigger is None:
        sizing.update({"quantity": 0, "position_value": 0.0, "risk_amount": 0.0, "status": "NO_SETUP"})
    if trigger is not None and sizing.get("quantity", 0) <= 0:
        blockers.append("Quy mô vị thế bằng 0 theo NAV, mức rủi ro, giá kích hoạt và stop-loss đã nhập")

    quantity = int(position.get("quantity", 0) or 0)
    manage_mode = str(position.get("mode", "")).upper() == "MANAGE_EXISTING" or quantity > 0
    entry_price = _num(position.get("entry_price"))
    manual_stop = _num(position.get("stop_price"))
    position_report = {"mode": "MANAGE_EXISTING" if manage_mode else "NEW_ENTRY",
                       "quantity": quantity, "entry_price": entry_price}
    if manage_mode and quantity <= 0:
        blockers.append("Đã chọn chế độ đang có hàng nhưng chưa nhập số lượng cổ phiếu")
        position_report["status"] = "NEED_QUANTITY"
    if quantity > 0:
        if entry_price is None or entry_price <= 0:
            blockers.append("Đã khai báo số lượng nắm giữ nhưng thiếu giá vốn hợp lệ")
            position_report["status"] = "NEED_ENTRY_PRICE"
        else:
            structure_stop = min(entry_price - 1.5 * atr, recent_support if recent_support else entry_price - 1.5 * atr)
            held_stop = manual_stop if manual_stop is not None and 0 < manual_stop < entry_price else max(0.01, structure_stop)
            risk_per_share = entry_price - held_stop
            held_target_1 = entry_price + 1.5 * risk_per_share if risk_per_share > 0 else None
            held_target_2 = entry_price + 2.0 * risk_per_share if risk_per_share > 0 else None
            # ATR-based ratcheting reference: it may rise with price but never loosens.
            trailing_candidate = close - 2.0 * atr
            trailing_reference = max(held_stop, trailing_candidate) if risk_per_share > 0 else held_stop
            pnl_pct = (close / entry_price - 1) * 100
            position_report.update({"market_price": close, "pnl_pct_before_costs": pnl_pct,
                "reference_invalidation": held_stop, "trailing_stop_reference": trailing_reference,
                "target_1_reference": held_target_1, "target_2_reference": held_target_2,
                "management_stages": [
                    {"stage": "BẢO VỆ VỊ THẾ", "condition": "Giá đóng cửa <= mốc vô hiệu", "action": "Đánh giá thoát/giảm rủi ro theo kế hoạch đã xác lập"},
                    {"stage": "THEO DÕI MỤC TIÊU 1", "condition": "Giá đạt mục tiêu tham chiếu 1", "action": "Đánh giá chốt một phần theo quy tắc người dùng thiết lập"},
                    {"stage": "THEO DÕI MỤC TIÊU 2", "condition": "Giá đạt mục tiêu tham chiếu 2", "action": "Đánh giá bảo vệ phần vị thế còn lại"}
                ],
                "risk_per_share": risk_per_share if risk_per_share > 0 else None,
                "distance_to_invalidation_pct": (close / held_stop - 1) * 100 if held_stop > 0 else None,
                "target_1_progress_pct": ((close-entry_price)/(held_target_1-entry_price)*100) if held_target_1 and held_target_1 > entry_price else None,
                "target_2_progress_pct": ((close-entry_price)/(held_target_2-entry_price)*100) if held_target_2 and held_target_2 > entry_price else None,
                "stop_source": "MANUAL_INPUT" if manual_stop is not None and 0 < manual_stop < entry_price else "ATR_AND_RECENT_SUPPORT_REFERENCE",
                "status": "REVIEW_RISK" if close <= held_stop else ("REVIEW_TARGET" if held_target_1 and close >= held_target_1 else "MONITOR")})
            if close <= held_stop:
                blockers.append("Giá đóng cửa đã chạm/vượt xuống mức vô hiệu tham chiếu của vị thế")

    actionable_setup = setup in ("BREAKOUT XÁC NHẬN", "PULLBACK TRONG XU HƯỚNG TĂNG", "HỒI PHỤC CÓ XÁC NHẬN", "NỀN TÍCH LŨY")
    if manage_mode and quantity <= 0:
        status = "POSITION_INPUT_REQUIRED"
        decision = "CHƯA ĐỦ THÔNG TIN VỊ THẾ – NHẬP SỐ LƯỢNG"
    elif quantity > 0:
        status = "MANAGE_POSITION"
        decision = "QUẢN LÝ VỊ THẾ – ĐÁNH GIÁ LẠI RỦI RO" if blockers else "TIẾP TỤC THEO DÕI VỊ THẾ THEO KẾ HOẠCH"
    elif blockers or not actionable_setup or trigger is None:
        status = "STAND_ASIDE" if (trend_down or setup.startswith("BẬT GIÁ") or setup.startswith("KHÔNG CÓ")) else "WAIT_CONFIRMATION"
        decision = "ĐỨNG NGOÀI – KHÔNG MUA" if status == "STAND_ASIDE" else "CHỜ XÁC NHẬN – CHƯA MUA"
    else:
        status = "TRADE_PLAN_READY"
        decision = "CÓ THỂ LẬP KẾ HOẠCH GIAO DỊCH CÓ ĐIỀU KIỆN"

    if trigger is None:
        plan = {"reference_trigger": None, "entry_zone_low": None, "entry_zone_high": None,
                "invalidation": None, "target_1": None, "target_2": None,
                "rr_target_1": None, "rr_target_2": None, "atr14": atr,
                "prior_20d_high": prior_high, "prior_20d_low": prior_low}
    else:
        plan = {"reference_trigger": trigger, "entry_zone_low": trigger - 0.15*atr,
                "entry_zone_high": trigger + 0.10*atr, "invalidation": stop,
                "target_1": target_1, "target_2": target_2,
                "rr_target_1": rr_1, "rr_target_2": rr_2, "atr14": atr,
                "prior_20d_high": prior_high, "prior_20d_low": prior_low}
    # Existing holdings must not display a new-entry sizing as if it were the held position.
    if manage_mode:
        sizing = {"quantity": quantity, "position_value": quantity * close,
                  "risk_budget": None, "risk_amount": (quantity * max(0.0, entry_price - position_report.get("reference_invalidation", entry_price))) if entry_price else None,
                  "status": "EXISTING_POSITION_ONLY"}

    next_steps = (["Không mở vị thế mới khi trạng thái là ĐỨNG NGOÀI.",
                   "Chờ xu hướng và khối lượng xác nhận; không mua chỉ vì một phiên bật tăng."] if status == "STAND_ASIDE" else
                  ["Chờ giá đóng cửa thỏa điều kiện kích hoạt; không mua đuổi.",
                   "Nếu giá không xác nhận hoặc thủng mức vô hiệu, hủy kế hoạch."] if status == "WAIT_CONFIRMATION" else
                  ["Chỉ xem xét giao dịch khi giá nằm trong vùng kích hoạt và dữ liệu vẫn hợp lệ.",
                   "Tuân thủ số lượng theo ngân sách rủi ro; không tăng vị thế ngoài kế hoạch."] if status == "TRADE_PLAN_READY" else
                  ["Đối chiếu giá hiện tại, giá vốn, tỷ trọng và mức vô hiệu của vị thế.",
                   "Không bình quân giá xuống chỉ vì giá giảm; đánh giá lại luận điểm và rủi ro."])
    if not documents:
        reasons.append("Chưa có tài liệu doanh nghiệp liên kết; rủi ro sự kiện/cơ bản chưa được đối chiếu.")

    return {"symbol": symbol, "status": status, "decision": decision,
        "conclusion": decision, "horizon_sessions": "5-20", "risk_style": risk_style,
        "setup": setup, "score": score, "score_is_probability": False,
        "market_gate": gate, "reasons": reasons, "positives": positives,
        "negatives": negatives, "blockers": blockers, "next_steps": next_steps,
        "plan": plan, "position": position_report, "sizing": sizing,
        "market_behavior": behavior, "flow_trap": flow_trap, "valuation": valuation, "fundamental_flags": fundamental_flags,
        "evidence": {"symbol": symbol, "close": close, "ma5": ma5, "ma20": ma20, "ma50": ma50,
            "data_quality_status": quality_status, "data_conflicts_count": len(data_conflicts),
            "flow_bias": flow_trap.get("flow_bias"), "trap_risk": flow_trap.get("trap_risk"),
            "rsi14": rsi, "rel_volume20": relvol, "adx14": adx, "macd_hist": macdh,
            "ma20_rising": ma20_rising, "bounce_from_20d_low_pct": bounce_pct,
            "rs_market": rs_market or {}, "rs_sector": rs_sector or {}, "documents": documents[:8]},
        "limitations": ["Điểm Swing là điểm sàng lọc heuristic, không phải xác suất sinh lời.",
            "Các vùng giá là kịch bản tham chiếu có điều kiện, không phải lệnh tự động.",
            "Cần dữ liệu giá chuẩn VND/cổ phiếu và kiểm định walk-forward trước khi dùng vận hành.",
            "Tín hiệu bẫy giá/dòng tiền lớn chỉ là proxy OHLCV, không xác định chủ thể hoặc nội gián.",
            "Định giá chỉ có ý nghĩa khi EPS/BVPS/BCTC cùng kỳ, cùng đơn vị và được xác minh."]}


def scan_swing_universe(data: pd.DataFrame, market_regime: dict | None = None,
                        capital_vnd: float = 100_000_000, risk_pct: float = 1.0,
                        max_allocation_pct: float = 20.0, lot_size: int = 100,
                        risk_style: str = DEFAULT_STYLE) -> pd.DataFrame:
    """Rank eligible symbols for research; never treats ranking as a buy signal."""
    rows = []
    if data is None or data.empty or "symbol" not in data:
        return pd.DataFrame(columns=["symbol", "score", "setup", "status", "close", "rel_volume20"])
    for symbol, frame in data.groupby("symbol"):
        try:
            enriched = add_indicators(frame.sort_values("date").copy())
            report = analyze_swing_setup(enriched, market_regime=market_regime,
                                         capital_vnd=capital_vnd, risk_pct=risk_pct,
                                         max_allocation_pct=max_allocation_pct,
                                         lot_size=lot_size, risk_style=risk_style)
            if report.get("score") is None:
                continue
            p = report["plan"]
            e = report["evidence"]
            rows.append({"symbol": str(symbol), "score": report["score"],
                         "setup": report["setup"], "status": report["conclusion"],
                         "close": e["close"], "rel_volume20": e["rel_volume20"],
                         "flow_bias": report.get("flow_trap", {}).get("flow_bias"),
                         "trap_risk": report.get("flow_trap", {}).get("trap_risk"),
                         "trigger_ref": p["reference_trigger"],
                         "invalidation_ref": p["invalidation"],
                         "target_1_ref": p["target_1"],
                         "blockers": "; ".join(report["blockers"]),
                         "reasons": "; ".join(report["positives"][:3])})
        except Exception:
            # A malformed symbol is skipped; scanner continues for other symbols.
            continue
    if not rows:
        return pd.DataFrame(columns=["symbol", "score", "setup", "status", "close", "rel_volume20"])
    return pd.DataFrame(rows).sort_values(["score", "symbol"], ascending=[False, True]).reset_index(drop=True)
