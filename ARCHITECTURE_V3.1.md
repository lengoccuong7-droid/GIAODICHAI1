# Kiến trúc BOT TRADER SWING MULTI V3.1.0

## 1. Mục tiêu
Phát triển từ V3.0 thành trợ lý nghiên cứu giao dịch có khả năng tổng hợp bằng chứng và giải thích điều kiện hành động. Vẫn offline-first, không API AI, không đặt lệnh tự động.

## 2. Sơ đồ liên kết
```text
OHLCV ──> Data Loader ──> Data Quality / Unit Normalizer
                              │
                              v
             Indicators / Money Flow / Support-Resistance
                              │
               ┌──────────────┼─────────────────┐
               v              v                 v
          Strategy Engine  Market Regime   Multi-timeframe
               │              │                 │
               └──────┬───────┴─────────┬───────┘
                      v                 v
               Decision Engine      Relative Strength
                      │                 │
                      └────────┬────────┘
                               v
                         Risk Manager
                               │
                               v
                    Explainable Assistant
                               ▲
                               │
                 Evidence / Contradiction Ledger
                               ▲
                               │
           Knowledge Hub (SQLite, ticker + type + period + source)
                               │
                               v
               Report JSON / Human review / Audit
```

## 3. Trợ lý suy luận (assistant_reasoning.py)
- Tầng 1: kiểm tra đầu vào và dữ liệu còn thiếu.
- Tầng 2: đọc bằng chứng kỹ thuật, thanh khoản, benchmark, ngành, đa khung, định giá, tài chính, vị thế.
- Tầng 3: tìm mâu thuẫn liên nguồn, ví dụ khung tuần/tháng trái chiều hoặc kỹ thuật tốt nhưng regime xấu.
- Tầng 4: lập ba kịch bản có điều kiện (tích cực/cơ sở/tiêu cực).
- Tầng 5: đưa ra trạng thái nghiên cứu và điều kiện hành động/vô hiệu.
- Tầng 6: lưu sổ bằng chứng kèm nguồn và xuất JSON.

Không dùng mô hình AI tạo sinh; không khẳng định "suy nghĩ như con người". Đây là reasoning engine minh bạch, tái lập được.

## 4. Knowledge Hub (knowledge_hub.py)
- SQLite cục bộ.
- Metadata: ticker, loại tài liệu, kỳ báo cáo, nguồn, ngày nguồn, thời điểm lập chỉ mục, SHA-256.
- Hỗ trợ PDF text, DOCX, XLSX/XLS, CSV, TXT, MD, JSON.
- Trích đoạn tìm bằng từ khóa; không OCR PDF scan, không xác thực chữ ký/số liệu, không tự trích xuất chỉ tiêu kế toán thành dữ kiện đã xác minh.
- Tài liệu trùng byte được khử trùng lặp bằng SHA-256.
- Giới hạn file 20 MB.

## 5. Các nguyên tắc liên kết
- Mỗi báo cáo gắn mã, thời điểm sinh, kỳ nắm giữ, khẩu vị rủi ro.
- Mọi kết luận quan trọng phải có nguồn (OHLCV, chỉ báo, RS, regime, tài liệu, dữ liệu người dùng nhập).
- Không có dữ liệu thì ghi thiếu; không tự nội suy.
- Mâu thuẫn phải hiển thị, không tự bình quân để tạo kết luận giả.
- Điểm Scanner không phải xác suất tăng giá.
- Dữ liệu tài liệu chỉ là bằng chứng tham khảo đến khi người dùng kiểm tra tài liệu gốc.

## 6. Nghiệm thu
- Compile toàn bộ mã.
- Regression tests V2.3/V3.0.
- Unit test assistant reasoning và Knowledge Hub.
- Chạy Streamlit thực tế với dữ liệu OHLCV nhiều mã.
- Kiểm tra PDF text/DOCX/XLSX và khử trùng lặp.
- Kiểm thử điện thoại, đặc biệt thao tác upload, tab và download.
