# BOT TRADER SWING MULTI V4.3.0

## Mục tiêu
Tái cấu trúc thành 3 tab, dùng chung một phiên phân tích có định danh và giảm tính toán/kết luận trùng lặp.

## Thay đổi
- Điều hướng cấp cao còn 3 tab: PHÂN TÍCH, TRỢ LÝ AI, SWING TRADING.
- Các nhóm Tổng quan, Thị trường, Quant Lab/Backtest, Kiểm toán và Phân tích doanh nghiệp được gom vào tab PHÂN TÍCH dưới dạng nhóm tab con.
- Scanner đa mã và Knowledge Hub nằm trong TRỢ LÝ AI; Swing Scanner vẫn dùng cùng bộ máy Swing ở tab SWING TRADING.
- Bổ sung `modules/shared_analysis.py`: tạo một snapshot dùng chung gồm mã, `analysis_id`, fingerprint dữ liệu, ngày dữ liệu, market regime, RS, đa khung, chất lượng dữ liệu và kết quả decision engine.
- Trợ lý AI và Swing đọc cùng market regime, RS, đa khung, data quality và decision engine từ snapshot; không tự tính lại các phần này.
- Báo cáo JSON ghi `shared_analysis` và `analysis_id` để truy xuất phiên phân tích.
- Swing Expert từ chối dữ liệu không có mã hợp lệ, không tự gán `UNKNOWN`.
- Thanh điều hướng cấp cao có sticky positioning, z-index và scroll margin cho màn hình nhỏ.
- Giữ nguyên các module phân tích, Quant Lab, Backtest, Knowledge Hub, Scanner, dữ liệu và nhật ký hiện có.

## Kiểm thử
- Bộ kiểm thử hồi quy V4.2.1: 34 test đạt trước thay đổi.
- V4.3.0: 37 test đạt; bổ sung 3 test cho shared analysis context và xác thực symbol.
- `python -m compileall -q .`: đạt.

## Giới hạn cần biết
- Bộ máy vẫn là heuristic/rule-based, không phải mô hình tự học hay dự báo giá.
- Backtest hiện có là mô phỏng đơn giản; chưa đủ điều kiện tuyên bố hiệu quả chiến lược nếu chưa kiểm định walk-forward ngoài mẫu, phí, trượt giá, thanh khoản và bias.
- Sticky navigation được triển khai bằng CSS cho Streamlit; cần nghiệm thu trực tiếp trên trình duyệt điện thoại và máy tính vì DOM/CSS của Streamlit có thể thay đổi theo phiên bản.
- Không đặt lệnh tự động.
