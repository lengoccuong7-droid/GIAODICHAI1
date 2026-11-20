# Hướng dẫn nhanh V4.2.1

## Mục tiêu
Dùng ứng dụng để nhận một bản tư vấn Swing Trading 5–20 phiên dễ hiểu: **ĐỨNG NGOÀI**, **CHỜ XÁC NHẬN**, hoặc **CÓ THỂ LẬP KẾ HOẠCH GIAO DỊCH CÓ ĐIỀU KIỆN**.

## Quy trình sử dụng
1. Mở Sidebar và nạp OHLCV của mã cần phân tích.
2. Chọn đúng đơn vị giá nguồn. App chuẩn hóa giá về VND/cổ phiếu; khối lượng giữ nguyên số cổ phiếu.
3. Nếu có, nạp VN-Index và dữ liệu ngành để tăng chất lượng bối cảnh/relative strength.
4. Nhập NAV, mức rủi ro, tỷ trọng tối đa, lô giao dịch. Nếu file không có cột mã, bắt buộc nhập mã cổ phiếu. Nếu đang có hàng, chọn trạng thái nắm giữ và nhập số lượng/giá vốn; có thể nhập thêm giá dừng lỗ tham chiếu.
5. Nhập dữ liệu tài chính có nguồn và kỳ báo cáo tại nhóm Phân tích đầu tư. Không nhập số ước đoán như số liệu đã xác minh.
6. Mở nhóm Swing Trading. Đọc quyết định trước, sau đó đọc luận cứ, dấu hiệu giá/khối lượng, định giá, kế hoạch và điều kiện chặn.
7. Chỉ xem xét kế hoạch nếu dữ liệu đủ mới, đơn vị đúng, không có mâu thuẫn trọng yếu, vùng giá còn hiệu lực và quy mô vị thế hợp lệ.

## Ý nghĩa quyết định
- **ĐỨNG NGOÀI – KHÔNG MUA:** cấu trúc yếu, dấu hiệu rủi ro cao hoặc chưa có setup phù hợp.
- **CHỜ XÁC NHẬN – CHƯA MUA:** có dấu hiệu tiềm năng nhưng chưa đủ điều kiện kích hoạt.
- **CÓ THỂ LẬP KẾ HOẠCH GIAO DỊCH CÓ ĐIỀU KIỆN:** setup qua các bộ lọc hiện tại; vùng vào, vô hiệu, mục tiêu và sizing chỉ là kế hoạch tham chiếu có điều kiện.
- **QUẢN LÝ VỊ THẾ:** đánh giá vị thế đã nhập, hiển thị giá vốn, lãi/lỗ, mốc vô hiệu và hai mục tiêu tham chiếu theo bội số rủi ro; không tự động ra lệnh mua/bán.
- Nếu chọn đang có hàng nhưng chưa nhập số lượng, app sẽ yêu cầu bổ sung thay vì tạo kế hoạch mở mới.

## Phân biệt bật giá và hồi phục
- Bật giá kỹ thuật: giá nảy lên nhưng cấu trúc giảm chưa bị phá; không coi là đảo chiều.
- Hồi phục sớm: giá và MA20 cải thiện nhưng động lượng/khối lượng chưa đồng thuận.
- Hồi phục có xác nhận: giá trên MA20, MA20 cải thiện, RSI/MACD và khối lượng cùng hỗ trợ.
- Xu hướng tăng: cấu trúc giá và các khung thời gian cần được kiểm tra đồng thuận; không suy ra chỉ từ một chỉ báo.

## Dấu hiệu bẫy giá/dòng tiền
Các nhãn upthrust, spring, hấp thụ, phân phối, bán mạnh/kiệt cung là giả thuyết từ OHLCV. Chúng không xác định cá nhân/tổ chức, không chứng minh thao túng hoặc nội gián. Muốn kết luận sâu cần dữ liệu sổ lệnh và giao dịch chi tiết từ nguồn đáng tin cậy.

## Định giá
P/E, P/B, EV/EBITDA chỉ tính khi đầu vào hợp lệ. Không kết luận cổ phiếu rẻ/đắt nếu thiếu kỳ báo cáo nhất quán, so sánh ngành/lịch sử và kiểm tra nguồn.

## Giới hạn
Ứng dụng là công cụ nghiên cứu/giáo dục ngoại tuyến theo quy tắc, không phải mô hình tự học, không đảm bảo lợi nhuận, không tự đặt lệnh. Cần kiểm định walk-forward và chạy nghiệm thu giao diện trên môi trường Streamlit thật trước khi sử dụng vận hành.

## Lưu ý về mục tiêu chốt lời vị thế hiện có
Mục tiêu 1/2 là mốc tham chiếu tính từ giá vốn và khoảng cách đến mốc vô hiệu. Đây chưa phải mô hình tối ưu hóa chốt lời từng phần; cần được kiểm định walk-forward trước khi dùng như quy tắc vận hành.
