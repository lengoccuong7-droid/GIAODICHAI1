# Hướng dẫn V4.1.1

## Điều hướng
Ứng dụng gom 9 phân hệ thành 5 nhóm: Tổng quan; Thị trường; Phân tích; Trợ lý & Scanner; Swing Trading. Trên điện thoại, cuộn ngang thanh tab khi cần. Thanh tab được thiết kế sticky khi cuộn trang.

## Chuẩn giá
Chọn đúng đơn vị giá gốc trong file. Tệp có giá 11.100 đồng/cổ phiếu phải chọn “Đồng/cổ phiếu”; chỉ chọn “Nghìn đồng/cổ phiếu” khi giá gốc lưu là 11,1. Ứng dụng quy đổi dữ liệu nội bộ về VND/cổ phiếu. Nếu thấy cảnh báo hệ số ×1.000, kiểm tra lại trước khi đọc các mức giá.

## Quyết định Swing 5–20 phiên
- ĐỨNG NGOÀI – KHÔNG MUA: xu hướng giảm, bật giá kỹ thuật chưa đảo chiều, không có mẫu hình đạt chuẩn hoặc dữ liệu bị chặn.
- CHỜ XÁC NHẬN – CHƯA MUA: có cấu trúc tiềm năng nhưng thiếu điều kiện kích hoạt, thanh khoản, R:R hoặc quy mô vị thế.
- CÓ THỂ LẬP KẾ HOẠCH GIAO DỊCH CÓ ĐIỀU KIỆN: mô hình, điểm số, dữ liệu, R:R và quy mô vị thế đều qua cổng kiểm soát. Đây vẫn không phải lệnh tự động.

## Phân biệt vận động giá
- BẬT GIÁ KỸ THUẬT: giá nảy lên từ đáy nhưng còn dưới cấu trúc xu hướng; không đồng nghĩa đảo chiều.
- HỒI PHỤC SỚM: vượt MA20 và MA20 cải thiện nhưng động lượng chưa đủ xác nhận.
- HỒI PHỤC CÓ XÁC NHẬN: giá, MA20, RSI, MACD và khối lượng đồng thuận theo bộ lọc.
- BREAKOUT: đóng cửa vượt đỉnh 20 phiên với Relative Volume đạt ngưỡng.

## Lưu ý
Mọi giá là VND/cổ phiếu sau chuẩn hóa. Nếu có mâu thuẫn nguồn hoặc chất lượng dữ liệu không đạt, ứng dụng khóa trạng thái sẵn sàng giao dịch. Không dùng mức giá tham chiếu như lệnh mua/bán tự động.
