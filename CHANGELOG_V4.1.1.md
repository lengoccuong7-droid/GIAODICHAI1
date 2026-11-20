# Changelog V4.1.1 — Mobile UI & Trading Decision Gate

## Giao diện
- Gom 9 tab thành 5 nhóm điều hướng; các phân hệ tương tự nằm trong tab con.
- Thanh điều hướng có sticky positioning khi cuộn, hỗ trợ cuộn ngang trên màn hình nhỏ.
- Thu gọn phần mâu thuẫn/dữ liệu thiếu thành expander; thay JSON coverage dài bằng bảng trạng thái gọn.
- Bổ sung cảnh báo đơn vị giá đầu vào khi lựa chọn hệ số ×1.000 có nguy cơ sai.

## Bộ máy quyết định Swing
- Quyết định rõ 3 trạng thái: ĐỨNG NGOÀI – KHÔNG MUA; CHỜ XÁC NHẬN – CHƯA MUA; CÓ THỂ LẬP KẾ HOẠCH GIAO DỊCH CÓ ĐIỀU KIỆN.
- Phân biệt BREAKOUT, PULLBACK, NỀN TÍCH LŨY, HỒI PHỤC SỚM và BẬT GIÁ KỸ THUẬT.
- Không coi bật giá kỹ thuật là đảo chiều; không tạo vùng mua khi mô hình chưa đạt chuẩn.
- Một kế hoạch giá duy nhất gồm vùng kích hoạt, vô hiệu, mục tiêu 1/2 và R:R.
- Mâu thuẫn nguồn hoặc chất lượng dữ liệu ERROR/WARNING sẽ chặn trạng thái sẵn sàng giao dịch.
- Khi số lượng tính được bằng 0, giải thích nguyên nhân và khóa kế hoạch.

## Kiểm thử
- Giữ lại bộ kiểm thử V4.1.0; bổ sung kiểm tra chặn mâu thuẫn và không lập kế hoạch khi thiếu mô hình.
- Kiểm thử tự động: 27 bài đạt.
- Đã kiểm tra cú pháp Python. Chưa kiểm thử giao diện trình duyệt vì môi trường đóng gói không có Streamlit.

## Giới hạn
- Quyết định là kết quả của bộ quy tắc minh bạch, không phải dự báo chắc chắn hay khuyến nghị cá nhân.
- Cần dữ liệu giá đúng đơn vị VND/cổ phiếu, dữ liệu mới và kiểm định walk-forward trước vận hành thực tế.
