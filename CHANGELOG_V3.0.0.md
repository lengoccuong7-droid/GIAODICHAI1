# V3.0.0 – Professional Investment Analyst

## Giữ lại
- Toàn bộ sáu tab V2.3.0 và các module kỹ thuật, dòng tiền, hỗ trợ/kháng cự, Quant Lab, backtest, audit, báo cáo đầu tư.
- Cơ chế nhập dữ liệu thủ công, offline-first; không API AI và không kết nối đặt lệnh.

## Sửa / thay đổi
- Sửa khởi tạo dải Supertrend 10,3; bổ sung hướng Supertrend.
- Chuẩn hóa đơn vị giá theo lựa chọn rõ ràng (VND hoặc nghìn VND), quy đổi về VND/cổ phiếu.
- Sửa bộ đọc ngày ISO và ngày DD/MM/YYYY để tránh đảo tháng/ngày.
- Sửa RS để so sánh trên khoảng thời gian chung; có fallback theo ngày gần nhất trước đó.
- Tăng kiểm tra hợp lệ của position sizing.
- Backtest tính thêm thuế bán và công khai giả định.
- Đồng bộ version, README, MANIFEST và changelog lên 3.0.0.

## Bổ sung
- Tab 7 Multi-Stock Scanner được tích hợp vào giao diện.
- Bộ máy Decision Engine được hiển thị trong Dashboard.
- Tổng hợp khung tuần/tháng.
- EV/EBITDA và cờ chất lượng tài chính từ dữ liệu nhập tay.
- Kiểm thử hồi quy bổ sung.

## Giới hạn còn lại
- Chưa có API dữ liệu thị trường/báo cáo tài chính tự động.
- Chưa có walk-forward/out-of-sample đầy đủ, corporate action engine, survivorship-bias-free universe.
- Chưa nghiệm thu giao diện Streamlit trên thiết bị thực tế trong môi trường người dùng.
