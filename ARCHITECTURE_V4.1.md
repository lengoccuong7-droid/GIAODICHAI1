# Kiến trúc V4.1 — Trading Master + Swing Trading Expert

## Vị trí trong hệ thống
V4.1 giữ nguyên V4.0 và bổ sung tab 9 chuyên gia Swing Trading 5–20 phiên.

## Luồng phân tích mã đơn
OHLCV đã chuẩn hóa -> `add_indicators` -> `analyze_swing_setup`.
`assess_market_regime`, `relative_strength`, Knowledge Hub, cấu hình NAV/risk/allocation/lot và vị thế được truyền vào cùng báo cáo.

## Luồng scanner
Toàn bộ universe -> group theo symbol -> `add_indicators` -> `analyze_swing_setup` -> xếp hạng -> bảng CSV.
Báo cáo mã đơn và scanner dùng chung bộ máy `analyze_swing_setup` để tránh hai bộ tiêu chí khác nhau.

## Module mới
- `modules/swing_trading_expert.py`: phân tích setup, chấm điểm heuristic, cổng thị trường, kế hoạch giá, sizing, quản lý vị thế, scanner.
- `tests/test_swing_trading_expert.py`: kiểm thử kế hoạch, vị thế và scanner.

## Liên kết với V4.0
- `indicators.py`: SMA20/50, RSI14, ATR14, MACD Histogram, Relative Volume, ADX14.
- `market_regime.py`: cổng bối cảnh thị trường.
- `relative_strength.py`: so sánh benchmark/ngành.
- `risk_manager.py`: position sizing.
- `knowledge_hub.py`: tài liệu doanh nghiệp liên kết ticker.
- Sidebar: NAV, risk/trade, max allocation, lot size, quantity và entry price.

## Nguyên tắc kỹ thuật
- Không nhân đôi dữ liệu hoặc định nghĩa chỉ báo riêng trong module Swing.
- Không đổi đơn vị giá đã được chuẩn hóa ở pipeline đầu vào.
- Mã thiếu dữ liệu phải trả trạng thái thiếu dữ liệu; scanner bỏ qua mã lỗi riêng lẻ và tiếp tục các mã còn lại.
- Điểm Swing không được trình bày như xác suất.
- Không đặt lệnh, không gọi API môi giới.
