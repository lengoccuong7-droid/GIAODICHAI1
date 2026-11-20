"""Local, offline document knowledge hub backed by SQLite."""
from __future__ import annotations
import hashlib, io, os, re, sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_NAME = "trading_knowledge.db"
MAX_BYTES = 20 * 1024 * 1024
SUPPORTED = {".txt", ".md", ".csv", ".json", ".pdf", ".docx", ".xlsx", ".xls"}


def _connect(db_path=DB_NAME):
    con = sqlite3.connect(db_path)
    con.execute("""CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sha256 TEXT UNIQUE NOT NULL,
        filename TEXT NOT NULL,
        ticker TEXT NOT NULL DEFAULT '',
        doc_type TEXT NOT NULL DEFAULT '',
        period TEXT NOT NULL DEFAULT '',
        source_name TEXT NOT NULL DEFAULT '',
        source_date TEXT NOT NULL DEFAULT '',
        indexed_at TEXT NOT NULL,
        content TEXT NOT NULL
    )""")
    con.commit()
    return con


def extract_text(filename: str, raw: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if len(raw) > MAX_BYTES:
        raise ValueError("Tài liệu vượt giới hạn 20 MB.")
    if ext not in SUPPORTED:
        raise ValueError(f"Chưa hỗ trợ định dạng {ext}.")
    if ext in {".txt", ".md", ".csv", ".json"}:
        return raw.decode("utf-8-sig", errors="replace")
    bio = io.BytesIO(raw)
    if ext == ".pdf":
        try:
            import pdfplumber
        except ImportError as exc:
            raise ValueError("Cài pdfplumber để đọc PDF.") from exc
        pages = []
        with pdfplumber.open(bio) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(f"[TRANG {i}]\n{text}")
        return "\n\n".join(pages)
    if ext == ".docx":
        try:
            from docx import Document
        except ImportError as exc:
            raise ValueError("Cài python-docx để đọc DOCX.") from exc
        doc = Document(bio)
        chunks = [p.text for p in doc.paragraphs if p.text.strip()]
        for ti, table in enumerate(doc.tables, 1):
            chunks.append(f"[BẢNG {ti}]")
            chunks.extend(" | ".join(c.text.strip() for c in row.cells) for row in table.rows)
        return "\n".join(chunks)
    if ext in {".xlsx", ".xls"}:
        try:
            import pandas as pd
            book = pd.ExcelFile(bio)
            parts = []
            for sheet in book.sheet_names:
                frame = pd.read_excel(book, sheet_name=sheet)
                parts.append(f"[SHEET {sheet}]\n{frame.to_csv(index=False)}")
            return "\n\n".join(parts)
        except Exception as exc:
            raise ValueError(f"Không đọc được bảng tính: {exc}") from exc
    return ""


def index_document(filename, raw, ticker="", doc_type="", period="", source_name="", source_date="", db_path=DB_NAME):
    text = extract_text(filename, raw).strip()
    if not text:
        raise ValueError("Không trích xuất được văn bản. PDF scan cần OCR bên ngoài trước khi nạp.")
    digest = hashlib.sha256(raw).hexdigest()
    con = _connect(db_path)
    try:
        con.execute("""INSERT OR IGNORE INTO documents
            (sha256,filename,ticker,doc_type,period,source_name,source_date,indexed_at,content)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (digest, filename, ticker.strip().upper(), doc_type, period, source_name,
             source_date, datetime.now(timezone.utc).isoformat(), text))
        con.commit()
        row = con.execute("SELECT id FROM documents WHERE sha256=?", (digest,)).fetchone()
        return {"id": row[0], "filename": filename, "characters": len(text), "duplicate": con.total_changes == 0}
    finally:
        con.close()


def search_documents(query, ticker="", limit=8, db_path=DB_NAME):
    terms = [t.lower() for t in re.findall(r"[\w.-]+", query or "") if len(t) > 1]
    con = _connect(db_path)
    try:
        rows = con.execute("""SELECT id,filename,ticker,doc_type,period,source_name,source_date,content
                              FROM documents WHERE (?='' OR ticker='' OR ticker=?) ORDER BY indexed_at DESC""",
                           (ticker.upper(), ticker.upper())).fetchall()
    finally:
        con.close()
    results = []
    for row in rows:
        doc_id, filename, doc_ticker, doc_type, period, source, source_date, content = row
        lower = content.lower()
        score = sum(lower.count(term) for term in terms)
        if not terms or score:
            excerpt = ""
            if terms:
                pos = max((lower.find(t) for t in terms if lower.find(t) >= 0), default=0)
                excerpt = re.sub(r"\s+", " ", content[max(0, pos-180):pos+420]).strip()
            else:
                excerpt = re.sub(r"\s+", " ", content[:500]).strip()
            results.append({"id": doc_id, "filename": filename, "ticker": doc_ticker,
                            "doc_type": doc_type, "period": period, "source_name": source,
                            "source_date": source_date, "score": score, "excerpt": excerpt})
    results.sort(key=lambda x: (x["score"], x["id"]), reverse=True)
    return results[:limit]


def list_documents(db_path=DB_NAME):
    con = _connect(db_path)
    try:
        rows = con.execute("SELECT id,filename,ticker,doc_type,period,source_name,source_date,indexed_at FROM documents ORDER BY indexed_at DESC").fetchall()
        return [dict(zip(["id","filename","ticker","doc_type","period","source_name","source_date","indexed_at"], r)) for r in rows]
    finally:
        con.close()
