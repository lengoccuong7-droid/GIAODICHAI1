# BOT TRADER SWING MULTI V4.2.1

## Sửa lỗi và hoàn thiện luồng quyết định
- Không tự gán mã `UNKNOWN` khi file OHLCV thiếu cột mã; yêu cầu người dùng nhập mã hợp lệ.
- Chuẩn hóa và kiểm tra các giá trị mã rỗng/NaN/UNKNOWN; chỉ thay bằng mã nhập tay khi người dùng cung cấp.
- Tách giao diện kế hoạch mở vị thế mới và quản lý vị thế đang nắm giữ.
- Khi đang có hàng, hiển thị số lượng hiện có, giá vốn, giá hiện tại, lãi/lỗ, mốc vô hiệu và hai mục tiêu tham chiếu riêng.
- Cho phép dùng giá dừng lỗ người dùng nhập nếu hợp lệ; nếu không, dùng mốc tham chiếu ATR/hỗ trợ.
- Không hiển thị sizing của lệnh mới như sizing của vị thế hiện có.
- Bổ sung kiểm thử hồi quy cho mã UNKNOWN và kế hoạch quản lý vị thế.

## Giới hạn
- Mục tiêu chốt lời vị thế hiện có là tham chiếu theo bội số rủi ro, không phải lệnh tự động.
- Bộ máy vẫn là hệ thống luật heuristic; cần kiểm định walk-forward và đối chiếu dữ liệu trước khi sử dụng thực tế.
