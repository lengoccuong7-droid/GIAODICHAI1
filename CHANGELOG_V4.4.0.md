# BOT TRADER SWING MULTI – V4.4.0

## Nâng cấp chính: Dòng tiền OHLCV và nhận diện bẫy giá đa phiên
- Thêm `modules/market_flow_trap.py` để đánh giá proxy dòng tiền trên cửa sổ 20 phiên và sự kiện nghi vấn trong 5 phiên gần nhất.
- Tích hợp CLV-volume proxy, OBV proxy, RVOL, giá trị giao dịch xấp xỉ, phân kỳ giá/OBV, các phiên khối lượng cao nhưng đóng cửa yếu.
- Nhận diện mẫu hình nghi vấn bull trap/upthrust và bear trap/spring bằng vùng đỉnh/đáy 20 phiên trước, điều kiện đóng cửa quay lại vùng và RVOL.
- Đưa cảnh báo bẫy tăng/phân phối và proxy cung chi phối vào blockers của Swing Decision Engine.
- Mở rộng kết quả Scanner với `flow_bias` và `trap_risk`.
- Mở rộng giao diện Swing: trạng thái proxy dòng tiền, rủi ro bẫy giá, RVOL, biến động giá 20 phiên, số phiên cung mạnh và chi tiết sự kiện.
- Giữ nguyên giới hạn: OHLCV không xác định danh tính tổ chức, không chứng minh thao túng và không thay thế dữ liệu sổ lệnh/tick.

## Kiểm thử
- Bộ kiểm thử hiện có và mới: 40 passed.
- `compileall`: passed.
- Chưa thực hiện kiểm thử giao diện Streamlit trên trình duyệt/điện thoại trong môi trường build.
- Chưa có kiểm định walk-forward/OOS cho hiệu quả chiến lược; các ngưỡng là heuristic minh bạch, cần kiểm định trước khi vận hành.
