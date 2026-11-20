# Kiến trúc BOT TRADER SWING MULTI V3.0

## Mục tiêu thiết kế

Giữ nguyên các tab và module V2.3.0 đang có giá trị; sửa lỗi tính toán; đưa các module phân tích rời rạc vào luồng giao diện; chuẩn hóa dữ liệu và đơn vị; tăng khả năng kiểm thử. V3.0 là ứng dụng nghiên cứu/mô phỏng, không phải hệ thống giao dịch tự động.

## Luồng dữ liệu

```text
CSV / XLSX / JSON / TXT / Parquet
              |
              v
       data_loader.py
  alias + schema + OHLCV validation
              |
              v
       price_units.py
  explicit VND / thousand-VND conversion
              |
              v
       data_quality.py
              |
       +------+---------------------+
       |                            |
       v                            v
 indicators.py                market_regime.py
       |                            |
       +-------------+--------------+
                     |
          +----------+----------+
          |          |          |
          v          v          v
     strategy    decision    multi-timeframe
      engine      engine        analysis
          |          |          |
          +-----+----+----------+
                |
        stock_scanner.py
                |
      Streamlit 7-tab interface
                |
        report / CSV / backtest
```

## Module giữ nguyên từ V2.3.0

- `data_loader.py`, `data_quality.py`: nạp và kiểm tra OHLCV.
- `indicators.py`: bộ chỉ báo kỹ thuật hiện hữu; sửa Supertrend.
- `support_resistance.py`, `indicator_summary.py`: vùng giá và tổng hợp tín hiệu.
- `strategy_engine.py`, `decision_engine.py`: luật chiến lược và điều kiện theo dõi.
- `risk_manager.py`, `portfolio_manager.py`: sizing và danh mục mô phỏng.
- `backtest.py`, `performance_metrics.py`: mô phỏng và thống kê hiệu suất.
- `relative_strength.py`, `market_regime.py`, `market_analysis.py`: RS, regime, phân tích mã.
- `tab5_excel.py`, `ai_analyzer.py`: giữ để tương thích; `ai_analyzer` là rule-based/offline, không phải mô hình AI tự học.

## Module mới / nâng cấp V3.0

- `price_units.py`: quy đổi OHLC theo lựa chọn rõ ràng của người dùng về VND/cổ phiếu.
- `multi_timeframe.py`: tổng hợp OHLCV tuần/tháng từ dữ liệu ngày và tính xu hướng tương ứng.
- `fundamental_analysis.py`: P/E, P/B, EV/EBITDA và cờ kiểm tra chất lượng tài chính từ số liệu nhập tay.
- `stock_scanner.py`: được nối vào tab Scanner; xếp hạng heuristic đa mã.
- `risk_manager.py`: kiểm tra input, tính vị thế theo ngân sách rủi ro và giới hạn tỷ trọng.
- `backtest.py`: bổ sung thuế bán vào mô phỏng và phần giả định.

## Nguyên tắc an toàn dữ liệu và tài chính

1. Không tự suy đoán đơn vị giá.
2. Không tự điền dữ liệu thiếu hoặc tự tạo số liệu doanh nghiệp.
3. Tín hiệu luôn đi kèm lý do/giả định; điểm Scanner không phải xác suất.
4. Dữ liệu benchmark phải cùng quy ước đơn vị và thời gian.
5. Backtest phải công khai phí, thuế, trượt giá và giới hạn mô hình.
6. Không đặt lệnh, không lưu thông tin đăng nhập môi giới.

## Nghiệm thu V3.0

- Compile toàn bộ Python source.
- Chạy pytest regression.
- Kiểm tra Supertrend có dữ liệu sau warm-up.
- Kiểm tra giá 25 nghìn đồng được quy đổi thành 25.000 VND.
- Kiểm tra Scanner nhận nhiều mã và trả bảng xếp hạng.
- Kiểm tra Streamlit thực tế trên desktop/mobile sau khi cài requirements và nạp dữ liệu thật.
