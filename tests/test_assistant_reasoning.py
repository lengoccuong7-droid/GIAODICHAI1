import pandas as pd
from modules.assistant_reasoning import build_reasoning_report
from modules.knowledge_hub import index_document, search_documents, list_documents


def test_reasoning_report_exposes_conflicts_and_missing_data():
    dates = pd.bdate_range("2025-01-01", periods=90)
    close = pd.Series([100 + i * 0.2 for i in range(90)])
    frame = pd.DataFrame({
        "date": dates, "close": close, "SMA20": close.rolling(20).mean(),
        "SMA50": close.rolling(50).mean(), "RSI14": 58.0,
        "MACD_HIST": 0.5, "REL_VOLUME20": 1.4, "ADX14": 27.0,
        "ATR14": 2.0
    })
    report = build_reasoning_report(
        "AAA", frame, decision={"decision": "THEO DÕI ĐIỂM XÁC NHẬN", "reasons": ["trend ok"]},
        regime={"regime": "GIẢM", "confidence": "TRUNG BÌNH"},
        mtf={"W": {"trend": "TĂNG"}, "M": {"trend": "GIẢM"}},
        data_quality={"status": "OK", "score": 100}
    )
    assert report["facts"]
    assert report["conflicts"]
    assert report["scenarios"]
    assert report["missing"]


def test_knowledge_hub_indexes_and_searches(tmp_path):
    db = str(tmp_path / "knowledge.sqlite")
    raw = b"AAA doanh thu tang truong loi nhuan dong tien kinh doanh."
    result = index_document("AAA.txt", raw, ticker="AAA", doc_type="BCTC",
                            period="Q3/2026", source_name="Nguon cong bo", db_path=db)
    assert result["characters"] > 10
    found = search_documents("doanh thu loi nhuan", ticker="AAA", db_path=db)
    assert found and found[0]["filename"] == "AAA.txt"
    assert list_documents(db_path=db)[0]["ticker"] == "AAA"
