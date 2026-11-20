"""Explainable offline trading assistant.

This module does not use an LLM and does not predict prices. It consolidates
existing analytical modules into an auditable decision memo with evidence,
contradictions, missing inputs, and conditional scenarios.
"""
from __future__ import annotations
import math
import pandas as pd


def _num(value):
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def build_reasoning_report(
    symbol: str,
    enriched: pd.DataFrame,
    decision: dict | None = None,
    regime: dict | None = None,
    rs_market: dict | None = None,
    rs_sector: dict | None = None,
    mtf: dict | None = None,
    fundamentals: dict | None = None,
    data_quality: dict | None = None,
    position: dict | None = None,
    documents: list | None = None,
    horizon: str = "Swing 2–20 phiên",
    risk_style: str = "Cân bằng",
) -> dict:
    """Create an explainable, source-labelled analysis memo."""
    decision = decision or {}
    regime = regime or {}
    rs_market = rs_market or {}
    rs_sector = rs_sector or {}
    mtf = mtf or {}
    fundamentals = fundamentals or {}
    data_quality = data_quality or {}
    position = position or {}
    documents = documents or []

    facts, positives, negatives, conflicts, missing, actions = [], [], [], [], [], []
    last = enriched.iloc[-1] if enriched is not None and not enriched.empty else None
    if last is None:
        return {
            "symbol": symbol, "status": "BLOCKED", "headline": "Chưa có dữ liệu giá hợp lệ.",
            "facts": [], "positives": [], "negatives": [],
            "conflicts": [], "missing": ["Tải dữ liệu OHLCV hợp lệ."],
            "scenarios": [], "action_plan": ["Chưa phân tích khi chưa có dữ liệu."],
            "documents": documents, "disclaimer": "Không phải khuyến nghị đầu tư."
        }

    close = _num(last.get("close"))
    ma20, ma50 = _num(last.get("SMA20")), _num(last.get("SMA50"))
    rsi, macd = _num(last.get("RSI14")), _num(last.get("MACD_HIST"))
    relvol, adx = _num(last.get("REL_VOLUME20")), _num(last.get("ADX14"))
    atr = _num(last.get("ATR14"))
    date = str(pd.to_datetime(last.get("date")).date()) if pd.notna(last.get("date")) else "không rõ"

    facts.append({"source": "OHLCV đã nạp", "fact": f"{symbol} đóng cửa {close:,.2f} tại ngày {date}." if close is not None else "Không có giá đóng cửa hợp lệ."})
    if ma20 is not None and ma50 is not None and close is not None:
        if close > ma20 > ma50:
            positives.append("Cấu trúc giá trên MA20 và MA50, thứ tự MA20 > MA50 hỗ trợ xu hướng tăng.")
        elif close < ma20 < ma50:
            negatives.append("Giá dưới MA20 và MA50, thứ tự MA20 < MA50 cho thấy cấu trúc xu hướng yếu.")
        else:
            conflicts.append("Giá và MA20/MA50 chưa tạo cấu trúc đồng thuận rõ; có thể là pha chuyển tiếp hoặc đi ngang.")
        facts.append({"source": "Chỉ báo kỹ thuật", "fact": f"MA20={ma20:,.2f}; MA50={ma50:,.2f}."})
    else:
        missing.append("Cần đủ lịch sử để tính MA20/MA50.")

    if rsi is not None:
        facts.append({"source": "Chỉ báo kỹ thuật", "fact": f"RSI14={rsi:.1f}."})
        if rsi >= 70: negatives.append("RSI quá mua; rủi ro mua đuổi/tăng nóng.")
        elif rsi >= 55: positives.append("RSI trên 55, động lượng tương đối tích cực.")
        elif rsi < 45: negatives.append("RSI dưới 45, động lượng yếu.")
        else: conflicts.append("RSI vùng trung tính; chưa xác nhận động lượng.")
    else:
        missing.append("RSI14 chưa tính được.")

    if macd is not None:
        (positives if macd > 0 else negatives).append("MACD Histogram dương." if macd > 0 else "MACD Histogram âm.")
    else:
        missing.append("Thiếu MACD Histogram.")

    if relvol is not None:
        facts.append({"source": "Khối lượng", "fact": f"Khối lượng tương đối 20 phiên={relvol:.2f}x."})
        if relvol >= 1.3: positives.append("Thanh khoản/khối lượng cao hơn trung bình, có thể hỗ trợ xác nhận biến động.")
        elif relvol < .8: negatives.append("Khối lượng thấp hơn trung bình; tín hiệu giá thiếu xác nhận.")
    else:
        missing.append("Thiếu khối lượng tương đối 20 phiên.")

    if adx is not None:
        facts.append({"source": "Chỉ báo xu hướng", "fact": f"ADX14={adx:.1f}."})
        if adx < 18: conflicts.append("ADX thấp: xu hướng chưa mạnh, chiến lược bám xu hướng có thể kém hiệu quả.")
        elif adx >= 25: positives.append("ADX cho thấy cường độ xu hướng tương đối rõ; cần xem thêm hướng DI+/DI-.")
    else:
        missing.append("Thiếu ADX14.")

    regime_name = regime.get("regime")
    if regime_name:
        facts.append({"source": "Market Regime", "fact": f"Trạng thái thị trường: {regime_name}; độ tin cậy hiển thị: {regime.get('confidence', 'không rõ')}."})
        if any(k in str(regime_name).upper() for k in ["BEAR", "DOWN", "GIẢM"]):
            negatives.append("Bối cảnh thị trường chung bất lợi; giảm mức độ quyết liệt và ưu tiên bảo toàn vốn.")
        elif any(k in str(regime_name).upper() for k in ["BULL", "UP", "TĂNG"]):
            positives.append("Bối cảnh thị trường chung thuận lợi hơn cho chiến lược theo xu hướng.")
    else:
        missing.append("Chưa có Market Regime/benchmark đáng tin cậy.")

    for label, rs in [("VN-Index", rs_market), ("Ngành", rs_sector)]:
        rel = _num(rs.get("relative_return_pct"))
        if rel is not None:
            facts.append({"source": f"Relative Strength vs {label}", "fact": f"Lợi suất vượt/trội tương đối: {rel:+.2f}% trong cửa sổ tính của module."})
            if rel > 0: positives.append(f"Mã đang vượt trội {label} theo cửa sổ RS đã tính.")
            elif rel < 0: negatives.append(f"Mã đang yếu hơn {label} theo cửa sổ RS đã tính.")
        else:
            missing.append(f"Thiếu dữ liệu đồng bộ để tính RS so với {label}.")

    for frame in ("W", "M"):
        item = mtf.get(frame, {}) if isinstance(mtf, dict) else {}
        trend = item.get("trend") if isinstance(item, dict) else None
        if trend:
            facts.append({"source": f"Đa khung {frame}", "fact": f"Xu hướng khung {frame}: {trend}."})
            if "TĂNG" in str(trend).upper() or "UP" in str(trend).upper():
                positives.append(f"Khung {frame} đang ủng hộ xu hướng tăng.")
            elif "GIẢM" in str(trend).upper() or "DOWN" in str(trend).upper():
                negatives.append(f"Khung {frame} đang bất lợi.")
        else:
            missing.append(f"Chưa đủ dữ liệu khung {frame}.")

    dq_status = data_quality.get("status")
    dq_score = _num(data_quality.get("score"))
    if dq_status or dq_score is not None:
        facts.append({"source": "Data Quality", "fact": f"Trạng thái={dq_status or 'không rõ'}; điểm={dq_score if dq_score is not None else 'không có'}/100."})
    if dq_score is not None and dq_score < 70:
        negatives.append("Chất lượng dữ liệu dưới ngưỡng 70/100: không nên tin cậy kết luận định lượng cho đến khi rà soát.")
    elif dq_score is None:
        missing.append("Không có điểm kiểm toán chất lượng dữ liệu.")

    for key, label in [("pe", "P/E"), ("pb", "P/B"), ("ev_ebitda", "EV/EBITDA")]:
        val = _num(fundamentals.get(key))
        if val is not None:
            facts.append({"source": "Định giá nhập thủ công", "fact": f"{label}={val:.2f} lần; cần kiểm tra kỳ và đơn vị báo cáo."})
    if fundamentals.get("flags"):
        negatives.extend([str(x) for x in fundamentals["flags"]])
    if not any(_num(fundamentals.get(k)) is not None for k in ("pe", "pb", "ev_ebitda")):
        missing.append("Thiếu bộ dữ liệu định giá doanh nghiệp (EPS/BVPS/vốn hóa/nợ ròng/EBITDA).")

    if decision:
        facts.append({"source": "Decision Engine", "fact": f"Trạng thái quy tắc: {decision.get('decision', 'không có')}."})
        for reason in decision.get("reasons", []) or []:
            facts.append({"source": "Decision Engine", "fact": str(reason)})
        if decision.get("decision") in ("KHÔNG ĐỦ ĐIỀU KIỆN THEO DÕI", "CHƯA ĐỦ DỮ LIỆU"):
            negatives.append("Decision Engine chưa xác nhận điều kiện theo dõi.")
    else:
        missing.append("Decision Engine chưa tạo kết quả.")

    if position.get("quantity", 0):
        pnl = _num(position.get("pnl_pct"))
        facts.append({"source": "Vị thế do người dùng nhập", "fact": f"Đang nắm {position['quantity']} cổ phiếu; lãi/lỗ tạm tính {pnl:+.2f}% chưa gồm phí/thuế." if pnl is not None else f"Đang nắm {position['quantity']} cổ phiếu."})
    else:
        facts.append({"source": "Vị thế", "fact": "Chưa khai báo vị thế đang nắm giữ."})

    # Cross-source contradictions are surfaced rather than silently averaged.
    weekly = str((mtf.get("W") or {}).get("trend", "")).upper() if isinstance(mtf, dict) else ""
    monthly = str((mtf.get("M") or {}).get("trend", "")).upper() if isinstance(mtf, dict) else ""
    if (("TĂNG" in weekly or "UP" in weekly) and ("GIẢM" in monthly or "DOWN" in monthly)) or (("GIẢM" in weekly or "DOWN" in weekly) and ("TĂNG" in monthly or "UP" in monthly)):
        conflicts.append("Khung tuần và tháng bất đồng: tránh kết luận một chiều; ưu tiên giảm quy mô hoặc chờ đồng thuận.")
    if positives and negatives:
        conflicts.append("Có đồng thời bằng chứng tích cực và tiêu cực; cần xử lý theo điều kiện xác nhận, không cộng điểm máy móc.")

    if close is not None and atr is not None and atr > 0:
        scenarios = [
            {"name": "Tích cực", "condition": "Giá đóng cửa vượt kháng cự gần nhất với khối lượng >= 1.3 lần trung bình và không bị thị trường chung phủ định.", "implication": "Theo dõi xác nhận; không mua đuổi nếu khoảng cách tới MA20/ATR đã lớn."},
            {"name": "Cơ sở", "condition": "Giá dao động quanh MA20/hỗ trợ, RSI trung tính và thanh khoản không đột biến.", "implication": "Ưu tiên chờ điểm vào có R:R phù hợp; không cần giao dịch khi lợi thế chưa rõ."},
            {"name": "Tiêu cực", "condition": "Đóng cửa dưới hỗ trợ/điểm vô hiệu hoặc thị trường chung chuyển xấu.", "implication": "Rà soát luận điểm và giới hạn rủi ro; không bình quân giá xuống chỉ vì giá giảm."},
        ]
        facts.append({"source": "Biến động", "fact": f"ATR14={atr:,.2f}; dùng làm thước đo biến động, không phải dự báo."})
    else:
        scenarios = [{"name": "Chưa thể lập kịch bản định lượng", "condition": "ATR14 hoặc giá hợp lệ chưa có.", "implication": "Bổ sung dữ liệu trước khi xác định vùng giá."}]
        missing.append("Thiếu ATR14 để xây dựng kịch bản biến động.")

    if data_quality and dq_score is not None and dq_score < 70:
        status = "BLOCKED_DATA_QUALITY"
        actions.append("Tạm dừng kết luận giao dịch: rà soát dữ liệu giá, ngày, đơn vị và các phiên bất thường.")
    elif not decision or decision.get("decision") == "CHƯA ĐỦ DỮ LIỆU":
        status = "INSUFFICIENT_EVIDENCE"
        actions.append("Chưa đủ bằng chứng: bổ sung lịch sử giá, benchmark và hồ sơ tài chính.")
    elif negatives and conflicts:
        status = "WAIT_FOR_CONFIRMATION"
        actions.append("Chờ xác nhận; không mở vị thế chỉ vì một tín hiệu đơn lẻ.")
    elif positives and not negatives:
        status = "FAVORABLE_BUT_UNCONFIRMED"
        actions.append("Bối cảnh tương đối thuận lợi nhưng vẫn phải kiểm tra điểm vào, thanh khoản, R:R và giới hạn danh mục.")
    else:
        status = "NEUTRAL"
        actions.append("Giữ trạng thái quan sát; chỉ hành động khi điều kiện định trước được đáp ứng.")

    if decision.get("stop_loss") is not None:
        actions.append(f"Mức vô hiệu tham chiếu từ Decision Engine: {decision['stop_loss']:,.2f}; phải kiểm tra lại theo hỗ trợ và biến động thực tế.")
    if decision.get("reward_risk") is not None:
        actions.append(f"R:R tham chiếu: {decision['reward_risk']:.2f}; không dùng nếu điểm vào thực tế khác giả định.")
    if position.get("quantity", 0):
        actions.append("Đang có vị thế: đánh giá rủi ro danh mục, khoảng cách tới mức vô hiệu và thanh khoản thoát; tránh quyết định chỉ theo P/L ngắn hạn.")
    else:
        actions.append("Chưa có vị thế: ưu tiên chờ xác nhận, không coi vùng mua tham chiếu là lệnh mua.")

    if not documents:
        missing.append("Chưa liên kết tài liệu doanh nghiệp/nguồn công bố vào Knowledge Hub.")
    else:
        for doc in documents:
            facts.append({"source": f"Tài liệu: {doc.get('filename', 'không rõ')}", "fact": doc.get("excerpt", "Đã lập chỉ mục; cần mở tài liệu gốc để xác minh.")})

    headline_map = {
        "BLOCKED_DATA_QUALITY": "DỪNG PHÂN TÍCH: chất lượng dữ liệu chưa đạt.",
        "INSUFFICIENT_EVIDENCE": "CHƯA ĐỦ BẰNG CHỨNG ĐỂ ĐƯA RA QUYẾT ĐỊNH.",
        "WAIT_FOR_CONFIRMATION": "CÓ TÍN HIỆU TRÁI CHIỀU: ƯU TIÊN CHỜ XÁC NHẬN.",
        "FAVORABLE_BUT_UNCONFIRMED": "BỐI CẢNH TƯƠNG ĐỐI THUẬN LỢI, NHƯNG CHƯA PHẢI LỆNH GIAO DỊCH.",
        "NEUTRAL": "TRẠNG THÁI TRUNG LẬP: TIẾP TỤC QUAN SÁT.",
    }
    return {
        "symbol": symbol, "status": status, "headline": headline_map[status],
        "horizon": horizon, "risk_style": risk_style,
        "facts": facts, "positives": list(dict.fromkeys(positives)),
        "negatives": list(dict.fromkeys(negatives)),
        "conflicts": list(dict.fromkeys(conflicts)),
        "missing": list(dict.fromkeys(missing)),
        "scenarios": scenarios, "action_plan": actions,
        "documents": documents,
        "disclaimer": "Trợ lý suy luận ngoại tuyến theo luật có thể kiểm toán; không phải mô hình AI tự học, không dự báo chắc chắn và không tự đặt lệnh."
    }
