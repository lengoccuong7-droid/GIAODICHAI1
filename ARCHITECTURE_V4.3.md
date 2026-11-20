# Kiến trúc V4.3.0 – Three-tab / Shared Analysis

## 1. Điều hướng
1. PHÂN TÍCH: Tổng quan, thị trường/dòng tiền/RS, Quant Lab, Backtest, kiểm toán dữ liệu, phân tích doanh nghiệp.
2. TRỢ LÝ AI: Scanner đa mã, Knowledge Hub, báo cáo suy luận, biên bản và hỏi đáp dựa trên bằng chứng cục bộ.
3. SWING TRADING: một kết luận Swing, kế hoạch mở mới hoặc quản lý vị thế hiện có, Swing Scanner.

## 2. Shared Analysis Context
`modules/shared_analysis.py` là điểm hợp nhất cho các dữ liệu phân tích dùng chung. Snapshot chứa:
- `symbol`
- `analysis_id`
- `data_fingerprint`
- `data_timestamp`
- `market_regime`
- `rs_market`, `rs_sector`
- `multi_timeframe`
- `data_quality`
- `decision_engine`

Các tab đọc cùng snapshot. Không tạo bản tính chỉ báo riêng cho từng tab. Các phép phân tích đặc thù (ví dụ định giá với giả định nhập tay, hành vi giá, mô hình Swing) vẫn nằm trong module chuyên trách và phải gắn cùng `symbol`/`analysis_id` khi xuất báo cáo.

## 3. Luồng dữ liệu
OHLCV/benchmark/ngành/tài chính/tài liệu → kiểm tra & chuẩn hóa → enriched OHLCV → shared context → assistant memo / swing expert → hiển thị và xuất báo cáo.

## 4. Quy tắc an toàn dữ liệu
- Không tự đoán symbol; thiếu hoặc `UNKNOWN` thì chặn.
- Mã trong lựa chọn UI phải tồn tại trong OHLCV.
- Khi dữ liệu thay đổi, fingerprint và `analysis_id` đổi.
- Chất lượng dữ liệu `ERROR` hoặc xung đột phải chặn kế hoạch giao dịch.
- Giá được chuẩn hóa về VND/cổ phiếu trước khi tính rủi ro.

## 5. Giới hạn
Engine quyết định là luật giải thích được, không phải AI tự học. Các điểm số là điểm sàng lọc, không phải xác suất thắng. Kế hoạch là tham chiếu nghiên cứu, không thực thi lệnh.
