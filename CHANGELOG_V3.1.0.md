# CHANGELOG V3.1.0
- Giữ lại toàn bộ 7 phân hệ V3.0.0.
- Thêm phân hệ thứ 8: Trợ lý suy luận giao dịch + Knowledge Hub.
- Thêm assistant_reasoning.py: tổng hợp bằng chứng, xung đột, thiếu dữ liệu, kịch bản và kế hoạch hành động.
- Thêm knowledge_hub.py: lập chỉ mục tài liệu cục bộ bằng SQLite, gắn mã/loại/kỳ/nguồn, SHA-256 chống trùng.
- Thêm xuất hồ sơ suy luận JSON.
- Thêm kiểm thử assistant reasoning và Knowledge Hub.
- Làm rõ giới hạn: offline rule-based reasoning, không phải LLM/AI tự học; trích đoạn tài liệu cần kiểm tra với bản gốc.
