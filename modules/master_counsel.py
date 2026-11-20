"""Trading Master: auditable multi-source decision orchestration.

Offline deterministic decision-support layer. It is not an LLM, price predictor,
or order execution system. Every conclusion is tied to supplied evidence.
"""
from __future__ import annotations
import json, sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_NAME = "trading_master_journal.sqlite"


def _has(text, words):
    t = (text or "").lower()
    return any(w in t for w in words)


def build_master_counsel(symbol: str, memo: dict, decision: dict | None = None,
                         capital_vnd: float | None = None, risk_pct: float = 1.0,
                         max_allocation_pct: float = 20.0,
                         position: dict | None = None) -> dict:
    """Convert the existing evidence memo into a structured investment brief."""
    decision, position = decision or {}, position or {}
    positives = list(memo.get("positives", []))
    negatives = list(memo.get("negatives", []))
    conflicts = list(memo.get("conflicts", []))
    missing = list(memo.get("missing", []))
    facts = list(memo.get("facts", []))
    status = memo.get("status", "INSUFFICIENT_EVIDENCE")

    # Evidence coverage is transparent, not a probability of profit.
    evidence_groups = {
        "Giá và kỹ thuật": any("OHLCV" in str(x.get("source", "")) or "kỹ thuật" in str(x.get("source", "")).lower() for x in facts),
        "Thị trường chung": any("Regime" in str(x.get("source", "")) for x in facts),
        "Sức mạnh tương đối": any("Relative Strength" in str(x.get("source", "")) for x in facts),
        "Đa khung thời gian": any("Đa khung" in str(x.get("source", "")) for x in facts),
        "Chất lượng dữ liệu": any("Data Quality" in str(x.get("source", "")) for x in facts),
        "Tài liệu doanh nghiệp": bool(memo.get("documents")),
        "Quản trị vị thế": bool(position.get("quantity", 0)) or capital_vnd is not None,
    }
    coverage = round(sum(evidence_groups.values()) / len(evidence_groups) * 100)

    # A strict gate: no green light merely because there are many positive signals.
    blockers = []
    if status == "BLOCKED_DATA_QUALITY": blockers.append("Chất lượng dữ liệu không đạt");
    if status == "INSUFFICIENT_EVIDENCE": blockers.append("Thiếu bằng chứng tối thiểu")
    if conflicts: blockers.append("Còn mâu thuẫn giữa các nguồn")
    if missing: blockers.append("Còn dữ liệu quan trọng chưa có")
    if decision.get("decision") not in ("THEO DÕI ĐIỂM XÁC NHẬN", "CHỜ XÁC NHẬN"):
        blockers.append("Decision Engine chưa đưa mã vào trạng thái theo dõi xác nhận")
    if not memo.get("documents"):
        blockers.append("Chưa có tài liệu doanh nghiệp liên kết cho mã này")

    if status == "BLOCKED_DATA_QUALITY":
        stance = "TẠM DỪNG – KIỂM TRA DỮ LIỆU"
        rationale = "Không nên diễn giải tín hiệu khi dữ liệu đầu vào chưa đạt chuẩn."
    elif negatives and len(negatives) >= len(positives):
        stance = "PHÒNG THỦ – CHỜ TÍN HIỆU TỐT HƠN"
        rationale = "Bằng chứng bất lợi đang ngang hoặc nhiều hơn bằng chứng tích cực."
    elif conflicts or missing or not positives:
        stance = "QUAN SÁT – CHƯA ĐỦ CƠ SỞ"
        rationale = "Các nguồn chưa đồng thuận hoặc còn thiếu dữ liệu để hình thành luận điểm đủ chắc."
    else:
        stance = "ĐƯA VÀO DANH SÁCH THEO DÕI"
        rationale = "Có các yếu tố hỗ trợ, nhưng đây chưa phải chỉ thị mua/bán. Cần điểm kích hoạt và mức vô hiệu rõ ràng."

    priority = []
    if any("thị trường" in x.lower() for x in negatives): priority.append("Đánh giá lại rủi ro thị trường chung trước khi xem xét vị thế mới.")
    if any("khối lượng" in x.lower() for x in negatives): priority.append("Chờ thanh khoản xác nhận, tránh diễn giải một phiên tăng giá đơn lẻ.")
    if any("định giá" in x.lower() or "tài liệu" in x.lower() for x in missing): priority.append("Bổ sung BCTC/công bố chính thức và kiểm tra kỳ, đơn vị, tính nhất quán.")
    if conflicts: priority.append("Giải quyết mâu thuẫn giữa khung thời gian và nguồn dữ liệu trước khi ra quyết định.")
    if not priority: priority.append("Xác định trước điểm kích hoạt, điểm vô hiệu, quy mô rủi ro và điều kiện không giao dịch.")

    return {
        "symbol": symbol, "stance": stance, "rationale": rationale,
        "evidence_coverage_pct": coverage,
        "coverage_breakdown": evidence_groups,
        "positive_count": len(positives), "negative_count": len(negatives),
        "conflict_count": len(conflicts), "missing_count": len(missing),
        "blockers": blockers, "priority_actions": priority,
        "risk_policy": {"risk_per_trade_pct": float(risk_pct), "max_allocation_pct": float(max_allocation_pct),
                        "capital_vnd": float(capital_vnd) if capital_vnd is not None else None},
        "position": position,
        "principle": "Không giao dịch cũng là một quyết định hợp lệ khi lợi thế chưa rõ.",
        "limitations": ["Điểm bao phủ là mức độ có mặt của nhóm bằng chứng, không phải xác suất sinh lời.",
                        "Suy luận hiện tại là bộ máy quy tắc ngoại tuyến, không phải mô hình ngôn ngữ tự học.",
                        "Tài liệu được truy xuất theo từ khóa; số liệu trong tài liệu phải được đối chiếu bản gốc."],
    }


def answer_counsel_question(question: str, counsel: dict, memo: dict,
                            decision: dict | None = None) -> dict:
    """Answer common owner questions from the current dossier without inventing facts."""
    q = (question or "").strip()
    if not q:
        return {"answer": "Hãy nhập câu hỏi về mã đang phân tích.", "basis": [], "caveat": ""}
    status = counsel.get("stance", "QUAN SÁT")
    positives, negatives = memo.get("positives", []), memo.get("negatives", [])
    conflicts, missing = memo.get("conflicts", []), memo.get("missing", [])
    basis = []
    if _has(q, ["mua", "vào lệnh", "mở vị thế", "điểm vào"]):
        answer = f"Quan điểm hiện tại: {status}. Chưa thể xem đây là lệnh mua. Chỉ đưa vào kế hoạch khi có điểm kích hoạt được xác nhận, tỷ lệ lợi nhuận/rủi ro phù hợp và mức vô hiệu xác định trước."
        basis = positives[:3] + negatives[:3] + conflicts[:2]
    elif _has(q, ["bán", "thoát", "cắt lỗ", "giữ", "nắm giữ"]):
        answer = "Tôi chưa thể kết luận bán hay tiếp tục nắm giữ chỉ từ câu hỏi này. Cần đối chiếu giá vốn, khối lượng, tỷ trọng danh mục, mức vô hiệu của luận điểm và thanh khoản thoát. " + status + "."
        basis = negatives[:4] + conflicts[:2]
        if not counsel.get("position", {}).get("quantity", 0): basis.append("Chưa khai báo vị thế thực tế trong ứng dụng.")
    elif _has(q, ["rủi ro", "nguy cơ", "xấu", "mất tiền"]):
        answer = "Các rủi ro đang được hệ thống ghi nhận: " + ("; ".join(negatives[:5]) if negatives else "chưa phát hiện trong các trường dữ liệu hiện có") + ". Không phát hiện được không có nghĩa là không tồn tại."
        basis = negatives[:5] + conflicts[:3]
    elif _has(q, ["thiếu", "bổ sung", "cần gì", "tài liệu"]):
        answer = "Những phần cần bổ sung trước khi kết luận: " + ("; ".join(missing[:7]) if missing else "các nhóm dữ liệu chính đã hiện diện; vẫn cần xác minh nguồn và kỳ báo cáo") + "."
        basis = missing[:7]
    elif _has(q, ["tại sao", "vì sao", "giải thích", "căn cứ", "luận điểm"]):
        answer = counsel.get("rationale", "Chưa đủ dữ liệu để giải thích.") + " Quan điểm tổng hợp: " + status + "."
        basis = positives[:4] + negatives[:4] + conflicts[:3]
    else:
        answer = f"Tóm tắt quân sư cho {counsel.get('symbol')}: {status}. {counsel.get('rationale','')} Ưu tiên tiếp theo: " + " ".join(counsel.get("priority_actions", [])[:3])
        basis = positives[:3] + negatives[:3] + conflicts[:2]
    return {"question": q, "answer": answer, "basis": basis,
            "caveat": "Câu trả lời được tạo từ hồ sơ hiện tại và luật suy luận có thể kiểm toán; không phải dự báo chắc chắn hay khuyến nghị đầu tư cá nhân."}


def save_decision_record(symbol: str, counsel: dict, memo: dict, question: str = "", answer: dict | None = None,
                         db_path: str = DB_NAME) -> int:
    con = sqlite3.connect(db_path)
    try:
        con.execute("""CREATE TABLE IF NOT EXISTS decision_journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
            symbol TEXT NOT NULL, stance TEXT NOT NULL, question TEXT NOT NULL,
            counsel_json TEXT NOT NULL, memo_json TEXT NOT NULL, answer_json TEXT NOT NULL)""")
        cur = con.execute("INSERT INTO decision_journal(created_at,symbol,stance,question,counsel_json,memo_json,answer_json) VALUES(?,?,?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), symbol, counsel.get("stance", ""), question,
             json.dumps(counsel, ensure_ascii=False, default=str),
             json.dumps(memo, ensure_ascii=False, default=str),
             json.dumps(answer or {}, ensure_ascii=False, default=str)))
        con.commit()
        return int(cur.lastrowid)
    finally:
        con.close()


def list_decision_records(limit: int = 50, db_path: str = DB_NAME) -> list[dict]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        con.execute("""CREATE TABLE IF NOT EXISTS decision_journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
            symbol TEXT NOT NULL, stance TEXT NOT NULL, question TEXT NOT NULL,
            counsel_json TEXT NOT NULL, memo_json TEXT NOT NULL, answer_json TEXT NOT NULL)""")
        rows = con.execute("SELECT id,created_at,symbol,stance,question FROM decision_journal ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()
