# ĐẶC TẢ CHUYÊN GIA SWING TRADING V4.1

## 1. Cấu hình đã chốt
- Phạm vi: BOTH — tìm cổ phiếu mới và quản lý cổ phiếu đang nắm giữ.
- Thời gian nắm giữ mục tiêu: 5–20 phiên giao dịch.
- Phong cách: CÂN BẰNG — cân bằng cơ hội và bảo vệ vốn.
- Không đặt lệnh, không kết nối API môi giới, không tự ý thay đổi vốn/rủi ro.

## 2. Nhiệm vụ
1. Đánh giá bối cảnh VN-Index/thị trường chung.
2. Phân tích xu hướng, động lượng, thanh khoản và cấu trúc giá từng mã.
3. Nhận diện có điều kiện các setup Breakout, Pullback, Base/Consolidation; không ép phân loại khi không đủ bằng chứng.
4. Đánh giá RS so với VN-Index và ngành khi có dữ liệu đồng bộ.
5. Tạo kế hoạch tham chiếu gồm trigger, invalidation, target 1/2 và R:R.
6. Tính quy mô vị thế theo NAV, rủi ro/giao dịch, tỷ trọng tối đa và bước lô.
7. Tách biệt luồng tìm cơ hội mới với luồng quản lý vị thế đang nắm.
8. Nêu bằng chứng ủng hộ, bất lợi, điều kiện chặn và hành động tiếp theo.
9. Liên kết tài liệu Knowledge Hub theo ticker; hiển thị đoạn trích để người dùng mở bản gốc kiểm chứng.
10. Sàng lọc nhiều mã và xếp hạng để nghiên cứu, không biến thứ hạng thành lệnh mua.

## 3. Bộ tiêu chí cân bằng hiện tại (heuristic)
- Xu hướng: Close > SMA20 > SMA50.
- Động lượng: RSI14, MACD Histogram.
- Thanh khoản: Relative Volume 20 phiên; ngưỡng phong cách cân bằng mặc định >= 1.1x.
- Cường độ xu hướng: ADX14.
- Setup: breakout vượt đỉnh 20 phiên kèm RVOL >= 1.3x; pullback quanh SMA20 trong xu hướng tăng; hoặc nền 20 phiên có biên độ tham chiếu <= 12%.
- Bối cảnh: Market Regime; nếu thị trường giảm, thêm điều kiện chặn và giảm điểm.
- Sức mạnh tương đối: RS so với benchmark/ngành khi được nạp.
- Điểm tối thiểu để đưa vào danh sách chờ kích hoạt: 65/100, không phải xác suất thành công.

Các ngưỡng là quy tắc khởi tạo minh bạch, chưa được tối ưu hay kiểm định walk-forward. Cần kiểm thử ngoài mẫu trước khi xem xét sử dụng thực tế.

## 4. Kế hoạch giá và rủi ro
- Trigger tham chiếu: cao hơn mức cao nhất giữa close/high phiên gần nhất một phần 0.1 ATR.
- Invalidation tham chiếu: mức thấp hơn giữa đáy 10 phiên và close - 1.5 ATR.
- Target 1/2: lần lượt 1.5R và 2R từ trigger.
- Position sizing: dùng risk manager hiện hữu, giới hạn đồng thời theo ngân sách rủi ro và tỷ trọng tối đa; làm tròn theo bước lô.
- Phí, thuế, trượt giá, thanh khoản và gap risk phải được kiểm tra bổ sung; kết quả sizing chỉ là mô phỏng.

## 5. Quản lý vị thế hiện hữu
- Dùng quantity và entry_price do người dùng khai báo.
- Tính P/L tham chiếu trước phí/thuế.
- So sánh giá đóng cửa với mức vô hiệu tham chiếu.
- Nếu thiếu giá vốn, trả trạng thái cần bổ sung; không suy đoán.
- Không tự động khuyên mua thêm/bình quân giá xuống.

## 6. Liên kết dữ liệu
- OHLCV chuẩn hóa VND/cổ phiếu -> indicators -> swing expert.
- Benchmark/ngành -> market regime và RS.
- Sidebar NAV/risk/allocation/lot/position -> sizing và position management.
- Knowledge Hub -> tài liệu gắn ticker -> evidence trong báo cáo.
- Swing Scanner dùng cùng hàm phân tích với báo cáo mã đơn lẻ để tránh lệch logic.

## 7. Đầu ra
- Kết luận: chờ xác nhận/chưa giao dịch, chờ kích hoạt, hoặc ưu tiên quản lý vị thế.
- Điểm Swing 0–100 kèm giải thích, không phải xác suất.
- Setup, luận cứ tích cực/tiêu cực, blockers, trigger/invalidation/targets, R:R, sizing, trạng thái vị thế, dữ liệu và tài liệu liên kết.
- Xuất JSON báo cáo đơn mã và CSV scanner.

## 8. Giới hạn
- Bộ máy deterministic/rule-based, không phải LLM, không tự học và không dự báo chắc chắn.
- Chưa có walk-forward/out-of-sample validation chuyên biệt cho bộ quy tắc Swing 5–20.
- Mẫu hình là bộ lọc định lượng đơn giản, không phải nhận dạng thị giác nâng cao.
- Không tự lấy dữ liệu thị trường trực tuyến; cần nạp dữ liệu có nguồn và ngày cập nhật rõ ràng.
- Không đặt lệnh và không thay thế đánh giá của người dùng/chuyên gia tài chính.
