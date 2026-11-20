# BOT TRADER SWING MULTI V4.0 — TRADING MASTER

## Mục tiêu
Lớp điều phối suy luận đa nguồn trên nền V3.1.0. Ứng dụng hợp nhất dữ liệu giá, chỉ báo, trạng thái thị trường, sức mạnh tương đối, đa khung thời gian, dữ liệu định giá, kiểm toán dữ liệu, vị thế người dùng và tài liệu đã nạp.

## Luồng dữ liệu
1. OHLCV → chuẩn hóa đơn vị → kiểm tra chất lượng → chỉ báo kỹ thuật.
2. OHLCV mã + benchmark/ngành → market regime và relative strength.
3. OHLCV ngày → ảnh chụp xu hướng tuần/tháng.
4. Dữ liệu tài chính nhập vào + tài liệu gắn mã/kỳ/nguồn → Knowledge Hub tìm kiếm đoạn liên quan.
5. Các kết quả trên → `assistant_reasoning.py` tạo sổ bằng chứng, tích cực/tiêu cực, mâu thuẫn, thiếu dữ liệu và kịch bản.
6. `master_counsel.py` → quan điểm tổng hợp, độ bao phủ nhóm bằng chứng, điều kiện chặn, việc ưu tiên, hỏi đáp theo hồ sơ hiện tại.
7. Nhật ký quyết định lưu cục bộ vào SQLite để xem lại các lần đánh giá.

## Nguyên tắc kiểm soát
- Không cộng điểm cơ học để giả lập xác suất thắng.
- Độ bao phủ bằng chứng không phải xác suất sinh lời.
- Nếu dữ liệu kém, thiếu hoặc mâu thuẫn, hệ thống phải ưu tiên dừng/chờ.
- Không tự đặt lệnh, không kết nối API giao dịch, không gửi dữ liệu ra ngoài.
- Không tự học hay tự cập nhật tri thức. Người dùng chủ động nạp tài liệu.

## Giới hạn kỹ thuật trung thực
V4.0 hiện là hệ thống suy luận quy tắc ngoại tuyến có thể kiểm toán, không phải LLM/agent tự chủ. Hỏi đáp hiểu một số nhóm ý định phổ biến và chỉ trả lời từ hồ sơ hiện tại; không phải hội thoại ngôn ngữ tự do như ChatGPT. Knowledge Hub hiện trích xuất văn bản và tìm kiếm từ khóa, chưa phải semantic RAG; chưa tự xác minh số liệu tài chính. PDF scan cần OCR trước khi nạp. Dữ liệu báo cáo và chỉ báo cần người dùng xác minh nguồn, kỳ, đơn vị.

## Cấu trúc mới
- `modules/master_counsel.py`: điều phối quan điểm, cổng kiểm soát, hỏi đáp theo hồ sơ và nhật ký quyết định.
- `trading_master_journal.sqlite`: tự tạo khi lưu biên bản; lưu cục bộ.
- `tests/test_master_counsel.py`: kiểm thử quan điểm thận trọng, hỏi đáp và nhật ký.
