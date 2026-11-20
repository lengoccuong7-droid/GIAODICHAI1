# Changelog V4.1.0 — Swing Trading Expert

## Cấu hình đã chốt
- Phạm vi BOTH: tìm cơ hội mới và quản lý vị thế đang nắm giữ.
- Kỳ vọng nắm giữ: 5–20 phiên.
- Phong cách: CÂN BẰNG.

## Bổ sung
- Tab 9: Chuyên gia chiến lược Swing Trading.
- Bộ phân tích setup Breakout, Pullback, Base/Consolidation.
- Bộ lọc thị trường chung, xu hướng, RSI, MACD Histogram, Relative Volume, ADX và RS benchmark/ngành.
- Kế hoạch tham chiếu trigger, invalidation, target 1/2, R:R.
- Position sizing dùng chung risk_manager hiện hữu.
- Luồng quản lý vị thế tách biệt với luồng tìm cơ hội mới.
- Swing Scanner nhiều mã dùng chung logic phân tích với báo cáo mã đơn.
- Liên kết Knowledge Hub và xuất JSON/CSV.

## Giữ nguyên
- Toàn bộ 8 tab, module, dữ liệu mẫu và các kiểm thử V4.0.
- Không thay đổi luồng nhập dữ liệu và chuẩn hóa đơn vị giá hiện hữu.

## Giới hạn
- Điểm Swing là heuristic, không phải xác suất.
- Bộ tiêu chí chưa được walk-forward/out-of-sample validation riêng.
- Không tự cập nhật giá trực tuyến, không tự học, không đặt lệnh.
