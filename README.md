# BOT TRADER SWING MULTI V4.2.1 — Smart Trading Strategist

Ứng dụng Streamlit hỗ trợ phân tích cổ phiếu và lập kế hoạch Swing Trading 5–20 phiên theo phong cách cân bằng. Trọng tâm là một kết luận dễ hiểu, có luận cứ và có điều kiện vô hiệu.

## Chạy ứng dụng

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Quy trình
1. Nạp OHLCV và chọn đúng đơn vị giá nguồn.
2. Nạp VN-Index/ngành nếu có.
3. Khai báo NAV, rủi ro, tỷ trọng và vị thế.
4. Nhập số liệu cơ bản có nguồn/kỳ báo cáo.
5. Xem nhóm Swing Trading để nhận quyết định, dấu hiệu hành vi giá/khối lượng, định giá và kế hoạch tham chiếu.

## Cấu trúc liên kết
- `app.py`: điều phối giao diện và kết nối module.
- `modules/data_loader.py`: đọc/chuẩn hóa OHLCV.
- `modules/price_units.py`: chuẩn hóa về VND/cổ phiếu.
- `modules/indicators.py`: chỉ báo kỹ thuật.
- `modules/market_behavior.py`: chẩn đoán mẫu hình bất thường OHLCV.
- `modules/swing_trading_expert.py`: một nguồn quyết định/kế hoạch Swing.
- `modules/fundamental_analysis.py`: định giá và cờ chất lượng tài chính.
- Các module còn lại: thị trường, RS, đa khung, scanner, rủi ro, Knowledge Hub, backtest và nhật ký.

Xem `ARCHITECTURE_V4.2.md`, `USER_GUIDE_V4.2.md` và `CHANGELOG_V4.2.1.md`.

## Kiểm thử
Chạy `pytest -q` từ thư mục gốc. Bộ kiểm thử tự động bao gồm kiểm thử hồi quy các phân hệ cũ và kiểm thử mới cho hành vi giá/khối lượng. Kiểm thử mã nguồn không thay thế nghiệm thu giao diện thực tế.

## Sửa lỗi V4.2.1
- Không tự gán mã UNKNOWN; yêu cầu mã hợp lệ khi thiếu cột mã trong file.
- Báo cáo JSON ghi rõ mã trong cả phần tổng quan và evidence.
- Tách kế hoạch mở mới khỏi quản lý vị thế đang nắm giữ.
- Quản lý vị thế có mục tiêu tham chiếu riêng, dùng giá dừng lỗ thủ công hợp lệ hoặc mốc ATR/hỗ trợ.
- Chế độ đang có hàng nhưng thiếu số lượng sẽ yêu cầu nhập dữ liệu, không rơi về luồng mở mới.

## Giới hạn quan trọng
Đây là hệ thống hỗ trợ nghiên cứu theo quy tắc giải thích được, không phải AI tự học, không nhận diện danh tính cá mập/nội gián, không chứng minh thao túng và không tự đặt lệnh. Mức giá phụ thuộc dữ liệu đầu vào và không phải cam kết lợi nhuận.
