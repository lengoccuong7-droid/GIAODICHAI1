from modules.master_counsel import build_master_counsel, answer_counsel_question, save_decision_record, list_decision_records


def _memo():
    return {
        "status": "WAIT_FOR_CONFIRMATION", "positives": ["Giá trên MA20 hỗ trợ xu hướng."],
        "negatives": ["Khối lượng thấp hơn trung bình."],
        "conflicts": ["Khung tuần và tháng bất đồng."],
        "missing": ["Thiếu BCTC mới nhất."],
        "facts": [{"source": "OHLCV đã nạp", "fact": "Close 100"}, {"source": "Data Quality", "fact": "OK"}],
        "documents": []
    }


def test_master_counsel_is_conservative_and_explainable():
    c = build_master_counsel("AAA", _memo(), {"decision": "CHỜ XÁC NHẬN"}, 100_000_000)
    assert c["stance"].startswith(("QUAN SÁT", "PHÒNG THỦ"))
    assert c["evidence_coverage_pct"] > 0
    assert c["blockers"]
    assert any("xác suất" in x for x in c["limitations"])


def test_question_answer_uses_current_evidence():
    memo = _memo()
    c = build_master_counsel("AAA", memo, {"decision": "CHỜ XÁC NHẬN"}, 100_000_000)
    a = answer_counsel_question("Rủi ro lớn nhất là gì?", c, memo)
    assert "Khối lượng thấp" in a["answer"]
    assert a["basis"]


def test_decision_journal_roundtrip(tmp_path):
    db = str(tmp_path / "journal.sqlite")
    c = build_master_counsel("AAA", _memo(), {"decision": "CHỜ XÁC NHẬN"}, 100_000_000)
    rid = save_decision_record("AAA", c, _memo(), db_path=db)
    rows = list_decision_records(db_path=db)
    assert rid == rows[0]["id"]
    assert rows[0]["symbol"] == "AAA"
