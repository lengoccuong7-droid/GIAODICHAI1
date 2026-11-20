# Hướng dẫn sử dụng V4.3.0

## Ba tab chính
- **PHÂN TÍCH:** xem tổng quan, kỹ thuật, dòng tiền, RS, thị trường, định giá, Quant Lab, Backtest và kiểm toán dữ liệu.
- **TRỢ LÝ AI:** xem suy luận có bằng chứng, quản lý tài liệu Knowledge Hub và quét danh sách cổ phiếu.
- **SWING TRADING:** xem một kết luận Swing thống nhất. Chọn trạng thái chưa có hàng hoặc đang có hàng ở Sidebar.

## Dữ liệu và mã cổ phiếu
1. Nạp OHLCV có ngày, mã, mở, cao, thấp, đóng, khối lượng.
2. Nếu file không có mã, nhập mã tại Sidebar.
3. Chọn đúng đơn vị giá gốc. Ứng dụng quy đổi về VND/cổ phiếu.
4. Kiểm tra chất lượng dữ liệu trước khi diễn giải kết quả.
5. Nạp benchmark/ngành nếu muốn có RS và bối cảnh thị trường đầy đủ.

## Shared analysis
Ba tab sử dụng chung snapshot phân tích. Khi đổi mã hoặc dữ liệu, snapshot được tạo lại với `analysis_id` mới. Báo cáo JSON lưu định danh để truy vết.

## Vị thế
- Chưa có hàng: nhập NAV và giới hạn rủi ro để xem kế hoạch có điều kiện nếu setup đạt chuẩn.
- Đang có hàng: nhập số lượng và giá vốn; không dùng sizing lệnh mới thay cho vị thế đang nắm giữ.

## Lưu ý
Điểm Swing không phải xác suất thắng. Các mức giá là tham chiếu dựa trên dữ liệu và quy tắc; không phải khuyến nghị cá nhân hoặc lệnh tự động. Backtest cần kiểm định ngoài mẫu trước khi dùng để đánh giá chiến lược.
