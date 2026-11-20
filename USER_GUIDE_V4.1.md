# Hướng dẫn sử dụng V4.1 — Chuyên gia Swing Trading

## Cấu hình mặc định
- Tìm cổ phiếu mới và quản lý cổ phiếu đang nắm giữ.
- Thời gian mục tiêu: 5–20 phiên.
- Phong cách: cân bằng.

## Chuẩn bị dữ liệu
1. Nạp OHLCV lịch sử có tối thiểu 50 phiên; nên có 200 phiên trở lên để đọc xu hướng dài hơn.
2. Nạp VN-Index và chỉ số ngành nếu có để đánh giá Market Regime và Relative Strength.
3. Chọn đúng đơn vị giá trong Sidebar.
4. Nhập NAV, rủi ro tối đa/giao dịch, tỷ trọng tối đa và bước lô.
5. Nếu đang có cổ phiếu, chọn trạng thái ĐANG CÓ HÀNG, nhập số lượng và giá vốn.
6. Nạp tài liệu doanh nghiệp ở tab 8, gắn đúng ticker, kỳ và nguồn.

## Dùng tab 9
1. Chọn mã cần phân tích ở Sidebar.
2. Mở tab 9 — CHUYÊN GIA SWING TRADING.
3. Đọc điểm Swing, setup và cổng thị trường. Điểm số chỉ xếp hạng heuristic, không phải xác suất.
4. Kiểm tra luận cứ tích cực, bất lợi và các điều kiện chặn.
5. Xem trigger, invalidation, target 1/2, R:R và sizing tham chiếu.
6. Khi có vị thế, bật trạng thái ĐANG CÓ HÀNG và nhập quantity/entry price để xem phần quản lý vị thế.
7. Chạy Swing Scanner để xếp hạng các mã đủ dữ liệu; mở từng mã để kiểm tra riêng.
8. Tải JSON hoặc CSV để lưu hồ sơ.

## Nguyên tắc sử dụng
- Trigger là điều kiện cần theo dõi, không phải lệnh mua tự động.
- Invalidation là mức tham chiếu để đánh giá luận điểm, không bảo đảm thoát được đúng giá.
- Sizing chưa phản ánh đầy đủ gap risk, thanh khoản, phí, thuế và trượt giá thực tế.
- Nếu dữ liệu thiếu, xung đột hoặc chất lượng kém, ưu tiên đứng ngoài và xác minh.
- Bộ quy tắc chưa được kiểm định walk-forward riêng; cần thử nghiệm trên dữ liệu ngoài mẫu trước khi dùng làm căn cứ thực tế.
