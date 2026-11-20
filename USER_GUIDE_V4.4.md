# Hướng dẫn V4.4.0 – Dòng tiền & bẫy giá

1. Chọn mã và nạp dữ liệu OHLCV hợp lệ, đã kiểm tra đơn vị giá và khối lượng.
2. Mở tab **SWING TRADING** và chạy phân tích mã.
3. Trong phần **Hành vi giá, dòng tiền và định giá**, xem hai trạng thái:
   - **Proxy dòng tiền**: nghiêng về cầu, nghiêng về cung/phân phối hoặc chưa rõ.
   - **Rủi ro bẫy giá**: cao, cần xác minh hoặc chưa thấy rõ.
4. Mở **Chỉ số chi tiết và sự kiện nghi vấn** để xem RVOL, CLV-volume proxy, OBV proxy, phân kỳ, các lần upthrust/spring và phiên cung mạnh.
5. Đọc mục **Luận cứ bất lợi / Blockers**. Nếu hệ thống cảnh báo bẫy tăng hoặc phân phối, không coi điểm vào tham chiếu là tín hiệu đã được xác nhận.
6. Với Scanner, dùng `flow_bias` và `trap_risk` để lọc danh sách nghiên cứu; thứ hạng không phải khuyến nghị mua.

## Giới hạn dữ liệu
- Tối thiểu 30 phiên; nên dùng 60–120 phiên trở lên.
- Dữ liệu OHLCV không cho biết chính xác bên mua/bán chủ động hay danh tính nhà đầu tư lớn.
- Một mẫu hình nghi vấn cần được xác nhận qua các phiên tiếp theo.
- Không dùng kết quả heuristic thay cho quản trị rủi ro và kiểm định chiến lược.

## Chạy ứng dụng
- Windows: chạy `install_windows.bat` một lần, sau đó `run_windows.bat`.
- macOS/Linux: chạy `bash run_mac_linux.sh`.
- Nếu cài thủ công: `pip install -r requirements.txt`, sau đó `streamlit run app.py`.
