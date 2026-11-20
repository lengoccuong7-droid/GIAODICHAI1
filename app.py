from __future__ import annotations
import io, json, math
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from config import APP_NAME, DEFAULT_CAPITAL_VND, APP_VERSION, PRICE_UNIT_OPTIONS, DEFAULT_PRICE_UNIT, DEFAULT_TAX_PCT
from modules.data_loader import load_market_file
from modules.indicators import add_indicators
from modules.support_resistance import find_support_resistance
from modules.data_quality import assess_data_quality
from modules.backtest import simple_swing_backtest
from modules.risk_manager import calculate_position_size
from modules.relative_strength import relative_strength
from modules.market_analysis import analyze_symbol, analyze_universe
from modules.stock_scanner import scan_universe
from modules.market_regime import assess_market_regime
from modules.multi_timeframe import timeframe_snapshot
from modules.fundamental_analysis import valuation_metrics, quality_flags
from modules.price_units import normalize_price_unit
from modules.assistant_reasoning import build_reasoning_report
from modules.knowledge_hub import index_document, search_documents, list_documents
from modules.master_counsel import build_master_counsel, answer_counsel_question, save_decision_record, list_decision_records
from modules.swing_trading_expert import analyze_swing_setup, scan_swing_universe
from modules.shared_analysis import build_shared_analysis_context

st.set_page_config(
    page_title=APP_NAME,
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown("""
<style>
.block-container{padding-top:1.1rem;padding-bottom:2rem}
[data-testid="stMetricValue"]{font-size:1.35rem}
.stTabs [data-baseweb="tab-list"]{gap:.25rem;flex-wrap:nowrap;overflow-x:auto;position:sticky;top:0;z-index:9999;background:var(--background-color);padding:.45rem .15rem;border-bottom:1px solid rgba(128,128,128,.25);scrollbar-width:thin;isolation:isolate}
.stTabs [data-baseweb="tab"]{white-space:nowrap;padding:.48rem .68rem;min-height:2.45rem}
.stTabs [data-baseweb="tab-panel"]{padding-top:1rem;scroll-margin-top:4rem}
[data-testid="stAlert"]{padding:.55rem .75rem;border-radius:10px}
[data-testid="stJson"]{max-width:100%;overflow-x:auto}
@media(max-width:700px){.stTabs [data-baseweb="tab-list"]{top:0;position:sticky}.block-container{padding-left:.65rem;padding-right:.65rem;padding-top:.55rem}.stTabs [data-baseweb="tab-list"]{top:0}.stTabs [data-baseweb="tab"]{font-size:.76rem;padding:.4rem .55rem}.stTabs [data-baseweb="tab-panel"]{padding-left:0;padding-right:0}.stMetric{padding:.35rem}.signal-card{padding:.7rem}}

.signal-card{padding:1rem;border-radius:12px;background:rgba(128,128,128,.10);border:1px solid rgba(128,128,128,.25)}
</style>
""", unsafe_allow_html=True)
st.title(APP_NAME)
st.caption(f"V{APP_VERSION} · Phân tích dữ liệu lịch sử và mô phỏng · Không đặt lệnh tự động")
st.caption("📱 Trên điện thoại: mở bảng nhập liệu bằng biểu tượng ☰ ở góc trên bên trái. Sidebar được đặt mặc định ở trạng thái mở khi khởi động.")

# -------------------- Helpers --------------------
def fmt(v, digits=2):
    try:
        if v is None or pd.isna(v) or not np.isfinite(float(v)): return "Chưa đủ dữ liệu"
        return f"{float(v):,.{digits}f}"
    except Exception: return "Chưa đủ dữ liệu"

def read_upload(up, hint=None):
    if up is None: return None
    return load_market_file(up, symbol_hint=hint)

def enrich(frame):
    x=add_indicators(frame.sort_values("date").copy())
    x["LOG_RETURN"] = np.log(x.close / x.close.shift(1))
    x["CLV"] = np.where((x.high-x.low)!=0, ((x.close-x.low)-(x.high-x.close))/(x.high-x.low), np.nan)
    vol_mean=x.volume.rolling(20,min_periods=20).mean()
    vol_std=x.volume.rolling(20,min_periods=20).std(ddof=0)
    x["VOLUME_ZSCORE"]=(x.volume-vol_mean)/vol_std.replace(0,np.nan)
    x["TURNOVER"] = x.close*x.volume
    x["ILLIQUIDITY_AMIHUD"] = (x.LOG_RETURN.abs()/x.TURNOVER.replace(0,np.nan)).rolling(20,min_periods=20).mean()
    return x

def annualized_gk(x):
    if len(x)<20:return None
    term=.5*np.log(x.high/x.low)**2-(2*np.log(2)-1)*np.log(x.close/x.open)**2
    v=term.replace([np.inf,-np.inf],np.nan).dropna()
    return float(np.sqrt(max(v.mean(),0)*252)*100) if len(v)>=10 else None

def annualized_parkinson(x):
    if len(x)<20:return None
    v=(np.log(x.high/x.low)**2).replace([np.inf,-np.inf],np.nan).dropna()
    return float(np.sqrt(v.mean()/(4*np.log(2))*252)*100) if len(v)>=10 else None

def hurst_rs(series):
    s=pd.Series(series).dropna().astype(float).values
    if len(s)<100:return None
    lags=[8,16,32,64]
    vals=[]
    for lag in lags:
        chunks=[]
        for i in range(0,len(s)-lag+1,lag):
            z=s[i:i+lag]; z=z-z.mean(); sd=z.std()
            if sd>0: chunks.append((z.cumsum().max()-z.cumsum().min())/sd)
        if chunks: vals.append((lag,float(np.mean(chunks))))
    if len(vals)<3:return None
    return float(np.polyfit(np.log([a for a,b in vals]),np.log([b for a,b in vals]),1)[0])

def return_entropy(series, bins=10):
    s=pd.Series(series).dropna().astype(float)
    if len(s)<50:return None
    counts=np.histogram(s,bins=bins)[0].astype(float)
    p=counts[counts>0]/counts.sum()
    return float(-(p*np.log(p)).sum()/np.log(bins))

def audit_flags(x):
    flags=[]
    if x.empty:return flags
    last=x.iloc[-1]
    if len(x)>1:
        prev=x.iloc[-2]
        if last.close>0 and prev.close>0 and abs(last.close/prev.close-1)>.25:
            flags.append("Biến động giá ngày gần nhất vượt 25%: kiểm tra điều chỉnh giá, chia tách hoặc dữ liệu lỗi.")
    if (x.volume==0).any(): flags.append(f"Có {(x.volume==0).sum()} phiên khối lượng bằng 0.")
    if x.date.duplicated().any(): flags.append("Có ngày giao dịch trùng lặp.")
    if x.date.is_monotonic_increasing is False: flags.append("Ngày chưa sắp xếp tăng dần.")
    return flags

# -------------------- Sidebar: all inputs --------------------
with st.sidebar:
    st.header("DỮ LIỆU & THÔNG SỐ")
    st.caption("Nhập dữ liệu và cấu hình tại đây. Trên iPhone, nếu thanh này đang ẩn, chạm biểu tượng ☰ ở góc trên bên trái.")
    price_unit=st.selectbox("Đơn vị giá trong file", list(PRICE_UNIT_OPTIONS), index=list(PRICE_UNIT_OPTIONS).index(DEFAULT_PRICE_UNIT), help="Chọn đúng đơn vị đang lưu trong file. App quy đổi về đồng/cổ phiếu trước khi tính NAV, định giá và quản trị vốn.")
    price_multiplier=PRICE_UNIT_OPTIONS[price_unit]
    main_file=st.file_uploader("1. Dữ liệu OHLCV chính",type=["csv","xlsx","xls","txt","json","parquet"],key="main_ohlcv")
    symbol_hint=st.text_input("Mã cổ phiếu (bắt buộc nếu file không có cột mã)","",key="symbol_hint",help="Ví dụ: DXG, FPT, HDB. App không tự gán UNKNOWN hoặc tự đoán mã.")
    sheet=st.text_input("Tên sheet Excel (để trống = sheet đầu)","",key="sheet_name")
    benchmark_file=st.file_uploader("2. Dữ liệu VN-Index (không bắt buộc)",type=["csv","xlsx","xls","txt"],key="benchmark_file")
    sector_file=st.file_uploader("3. Dữ liệu chỉ số ngành / nhóm ngành (không bắt buộc)",type=["csv","xlsx","xls","txt"],key="sector_file")
    st.divider()
    position_mode=st.radio("TRẠNG THÁI VỊ THẾ",["🟢 CHƯA CÓ HÀNG – Cầm tiền","🔵 ĐANG CÓ HÀNG – Cầm cổ phiếu"],key="position_mode")
    nav=st.number_input("Tổng NAV (VND)",min_value=0,value=int(DEFAULT_CAPITAL_VND),step=5_000_000,key="nav_vnd")
    risk_pct=st.number_input("Rủi ro tối đa / giao dịch (%)",min_value=.1,max_value=5.0,value=1.0,step=.1,key="risk_pct")
    max_alloc=st.number_input("Tỷ trọng tối đa / mã (%)",min_value=1.0,max_value=100.0,value=20.0,step=1.0,key="max_alloc")
    lot=st.number_input("Bước lô",min_value=1,value=100,step=1,key="lot_size")
    fee=st.number_input("Phí mỗi chiều (%)",min_value=0.0,max_value=2.0,value=.15,step=.01,key="fee_pct")
    slip=st.number_input("Trượt giá mỗi chiều (%)",min_value=0.0,max_value=2.0,value=.10,step=.01,key="slippage_pct")
    tax_pct=st.number_input("Thuế bán (%)",min_value=0.0,max_value=2.0,value=float(DEFAULT_TAX_PCT),step=.01,key="tax_pct")
    st.caption("Các mục bên dưới chỉ dùng khi đang có vị thế.")
    qty=st.number_input("Số lượng đang nắm giữ",min_value=0,value=0,step=100,key="held_quantity")
    entry=st.number_input("Giá vốn (đồng/cp)",min_value=0.0,value=0.0,step=100.0,key="average_entry")
    stop_assumption=st.number_input("Giá dừng lỗ giả định (đồng/cp)",min_value=0.0,value=0.0,step=100.0,key="manual_stop")
    st.caption("Nếu thiếu dữ liệu benchmark/ngành, tab RS sẽ ghi rõ chưa đủ dữ liệu.")

# Parse uploads with safe error reporting
main_data=bench_data=sector_data=None
load_errors=[]
try:
    if main_file:
        sheet_value = sheet.strip()
        if sheet_value.isdigit():
            sheet_value = int(sheet_value)
        main_data=load_market_file(main_file,sheet_name=(sheet_value if sheet_value != "" else 0),symbol_hint=symbol_hint.strip() or None)
except Exception as e: load_errors.append(f"OHLCV: {e}")
try:
    if benchmark_file: bench_data=load_market_file(benchmark_file,symbol_hint="VNINDEX")
except Exception as e: load_errors.append(f"VN-Index: {e}")
try:
    if sector_file: sector_data=load_market_file(sector_file,symbol_hint="SECTOR")
except Exception as e: load_errors.append(f"Ngành: {e}")
for e in load_errors: st.sidebar.error(e)

# Explicit price-unit normalization: never guess whether source prices are VND or thousand VND.
if main_data is not None and not main_data.empty:
    raw_median_close = float(pd.to_numeric(main_data["close"], errors="coerce").median())
    if price_multiplier == 1000.0 and 1000 <= raw_median_close <= 500000:
        st.sidebar.warning("Đơn vị cần kiểm tra: giá gốc trong file đang ở khoảng hàng nghìn–trăm nghìn. Nếu file đã là VND/cp, hãy chọn Đồng/cổ phiếu để tránh nhân 1.000 lần.")
    elif price_multiplier == 1.0 and 1 <= raw_median_close < 1000:
        st.sidebar.warning("Đơn vị cần kiểm tra: giá gốc dưới 1.000. Nếu file ghi theo nghìn đồng/cp, hãy chọn Nghìn đồng/cổ phiếu.")
main_data=normalize_price_unit(main_data,price_multiplier)
bench_data=normalize_price_unit(bench_data,price_multiplier)
sector_data=normalize_price_unit(sector_data,price_multiplier)
if main_data is not None:
    st.sidebar.caption(f"Chuẩn giá sau quy đổi: VND/cổ phiếu · Hệ số áp dụng: ×{price_multiplier:g}")

if main_data is not None:
    symbols=sorted(main_data.symbol.astype(str).unique().tolist())
    with st.sidebar:
        selected_symbol=st.selectbox("Mã phân tích",symbols,index=0)
else: selected_symbol=None

if main_data is not None and selected_symbol:
    raw=main_data[main_data.symbol.astype(str)==selected_symbol].sort_values("date").reset_index(drop=True)
    data=enrich(raw)
else:
    raw=data=None

# One shared analysis snapshot is the single source for all three tabs.
shared_context = None
shared_context_error = None
if data is not None and selected_symbol:
    try:
        shared_context = build_shared_analysis_context(
            selected_symbol, raw, data, universe=main_data, benchmark=bench_data, sector=sector_data,
            capital_vnd=float(nav), risk_pct=float(risk_pct),
            max_alloc_pct=float(max_alloc), lot_size=int(lot)
        )
    except Exception as exc:
        shared_context_error = str(exc)

# -------------------- Compact grouped navigation --------------------
main_tabs = st.tabs([
    "1 · PHÂN TÍCH",
    "2 · TRỢ LÝ AI",
    "3 · SWING TRADING",
])
with main_tabs[0]:

    inner_tabs = [st.container()]

    # TAB 1
    with inner_tabs[0]:
        st.subheader("Bản đồ giao dịch thực chiến")
        if data is None:
            st.info("Tải dữ liệu OHLCV ở Sidebar để bắt đầu. Các dữ liệu VN-Index/ngành là tùy chọn.")
        else:
            last=data.iloc[-1]; sr=find_support_resistance(data)
            close=float(last.close); atr=last.get("ATR14")
            sup=sr.get("support"); res=sr.get("resistance")
            buy_low=float(sup) if sup is not None else None
            buy_high=float(sup+0.5*atr) if sup is not None and pd.notna(atr) else None
            confirm=float(res+0.1*atr) if res is not None and pd.notna(atr) else None
            stop=float(sup-0.5*atr) if sup is not None and pd.notna(atr) else None
            tp1=float(res) if res is not None else None
            tp2=float(res+2*atr) if res is not None and pd.notna(atr) else None
            m1,m2,m3,m4=st.columns(4)
            m1.metric("Mã",selected_symbol); m2.metric("Giá đóng cửa",fmt(close)); m3.metric("ATR14",fmt(atr)); m4.metric("Xu hướng", "Tăng" if pd.notna(last.get("SMA20")) and pd.notna(last.get("SMA50")) and close>last.SMA20>last.SMA50 else "Chưa xác nhận")
            st.markdown("#### Chỉ báo tổng quan – không phải quyết định giao dịch")
            d1,d2,d3,d4=st.columns(4)
            d1.metric("RSI14",fmt(last.get("RSI14"),1))
            d2.metric("MACD Histogram",fmt(last.get("MACD_HIST"),2))
            d3.metric("Relative Volume",fmt(last.get("REL_VOLUME20"),2)+"x")
            d4.metric("ADX14",fmt(last.get("ADX14"),1))
            mtf=timeframe_snapshot(raw)
            with st.expander("Đồng thuận đa khung thời gian (tuần/tháng)"):
                mta,mtb=st.columns(2)
                mta.metric("Khung tuần",mtf.get("W",{}).get("trend","Chưa đủ dữ liệu"))
                mtb.metric("Khung tháng",mtf.get("M",{}).get("trend","Chưa đủ dữ liệu"))
                st.caption("Khung tuần/tháng được tổng hợp từ OHLCV ngày; cần lịch sử đủ dài để MA20/MA50 có ý nghĩa.")
            st.markdown("#### Biểu đồ giá và các vùng tham chiếu")
            chart=data.tail(120)
            fig=go.Figure(data=[go.Candlestick(
                x=chart["date"],open=chart["open"],high=chart["high"],
                low=chart["low"],close=chart["close"],name=selected_symbol
            )])
            # Dashboard is descriptive only. The Swing Expert is the single source of trade levels.
            if "SMA20" in chart.columns:
                fig.add_trace(go.Scatter(x=chart["date"], y=chart["SMA20"], mode="lines", name="MA20", line=dict(width=1)))
            if "SMA50" in chart.columns:
                fig.add_trace(go.Scatter(x=chart["date"], y=chart["SMA50"], mode="lines", name="MA50", line=dict(width=1)))
            fig.update_layout(height=430,margin=dict(l=10,r=10,t=25,b=10),xaxis_rangeslider_visible=False,
                              template="plotly_dark",showlegend=True)
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":True,"scrollZoom":True})
            st.caption("Dashboard chỉ hiển thị giá và MA20/MA50. Để tránh các tab đưa ra vùng giá mâu thuẫn, kế hoạch kích hoạt/stop/target duy nhất nằm tại tab Chuyên gia Swing Trading.")
            if position_mode.startswith("🔵") and qty > 0 and entry > 0:
                pnl_pct=(close/entry-1)*100
                st.info(f"Vị thế đang khai báo: {qty:,} cp · Giá vốn {entry:,.0f} VND/cp · Lãi/lỗ tạm tính {pnl_pct:+.2f}% trước phí và thuế. Mở tab Swing Trading để xem đánh giá quản lý vị thế.")
            else:
                st.info("Quyết định giao dịch, vùng kích hoạt, mức vô hiệu và mục tiêu được quản lý tập trung tại tab Chuyên gia Swing Trading.")



with main_tabs[0]:

    inner_tabs = st.tabs(['Dòng tiền & thanh khoản', 'Sức mạnh tương đối & ngành'])

    # TAB 2
    with inner_tabs[0]:
        st.subheader("Dòng tiền, thanh khoản & cảnh báo bất thường")
        if data is None: st.info("Cần dữ liệu OHLCV ở Sidebar.")
        else:
            r=data.iloc[-1]
            cols=st.columns(5)
            for col,label,key in zip(cols,["Volume","OBV","MFI14","Volume Z-Score","CMF20"],["volume","OBV","MFI14","VOLUME_ZSCORE","CMF20"]): col.metric(label,fmt(r.get(key),0 if key=="volume" else 2))
            st.line_chart(data.tail(120).set_index("date")[["volume"]],height=220)
            st.markdown("#### Cảnh báo mẫu hình cần kiểm tra")
            flags=[]
            if len(data)>=2:
                prev=data.iloc[-2]
                candle_range=(r.high-r.low)/r.close if r.close else 0
                lower_wick=(min(r.open,r.close)-r.low)/(r.high-r.low) if r.high>r.low else 0
                if lower_wick>.55 and r.volume>1.5*data.volume.tail(20).mean(): flags.append("Râu nến dưới dài kèm khối lượng cao: có thể là nhịp rũ bỏ/quét thanh khoản; cần xác nhận các phiên sau.")
                if candle_range<.01 and r.volume>data.volume.tail(20).median()*1.5: flags.append("Biên độ nến hẹp nhưng khối lượng cao: cần kiểm tra chất lượng giao dịch; không đủ căn cứ kết luận quay tay.")
            if flags:
                for f in flags: st.warning(f)
            else: st.info("Chưa phát hiện mẫu hình cảnh báo theo các ngưỡng sàng lọc đơn giản hiện tại.")
            avg_turnover=float(data.TURNOVER.tail(20).mean()) if len(data)>=20 else None
            amihud=r.get("ILLIQUIDITY_AMIHUD")
            avg_volume=float(data.volume.tail(20).mean()) if len(data)>=20 else None
            days=(qty/(avg_volume*.1)) if qty>0 and avg_volume is not None and avg_volume>0 else None
            a,b,c=st.columns(3); a.metric("Amihud 20 phiên",fmt(amihud,8)); b.metric("GTGD bình quân 20 phiên",fmt(avg_turnover,0)); c.metric("Ngày thoát vị thế ước tính",fmt(days,1))
            st.caption("Days to Liquidate giả định tham gia tối đa 10% khối lượng bình quân/ngày. Amihud phụ thuộc đơn vị giá và khối lượng của file; chỉ so sánh tương đối trong cùng quy ước dữ liệu.")


    # TAB 3
    with inner_tabs[1]:
        st.subheader("Sức mạnh tương đối & cấu trúc ngành")
        if data is None: st.info("Cần dữ liệu OHLCV chính.")
        else:
            bench_frame=bench_data[bench_data.symbol==bench_data.symbol.iloc[0]] if bench_data is not None else None
            sector_frame=sector_data[sector_data.symbol==sector_data.symbol.iloc[0]] if sector_data is not None else None
            rsb=relative_strength(raw,bench_frame,20)
            rss=relative_strength(raw,sector_frame,20)
            a,b,c=st.columns(3); a.metric("Sinh lời mã 20 phiên",fmt(rsb.get("return_pct"))+"%" if rsb.get("return_pct") is not None else "Chưa đủ dữ liệu")
            b.metric("Vượt/trội VN-Index",fmt(rsb.get("relative_return_pct"))+"%" if rsb.get("relative_return_pct") is not None else "Cần tải VN-Index")
            c.metric("Vượt/trội chỉ số ngành",fmt(rss.get("relative_return_pct"))+"%" if rss.get("relative_return_pct") is not None else "Cần tải chỉ số ngành")
            if bench_frame is None: st.warning("Chưa có dữ liệu VN-Index: tải file VN-Index ở Sidebar để tính RS so với thị trường.")
            if sector_frame is None: st.warning("Chưa có dữ liệu chỉ số ngành: tải file chỉ số ngành ở Sidebar để tính RS ngành.")
            st.markdown("#### Cấu trúc xu hướng đa khung tham chiếu")
            def trend(n):
                z=data.tail(n)
                if len(z)<min(n,50): return "Chưa đủ dữ liệu"
                highs=z.high; lows=z.low
                return "HH-HL (đỉnh/đáy cao dần)" if highs.iloc[-1]>highs.iloc[0] and lows.iloc[-1]>lows.iloc[0] else ("LH-LL (đỉnh/đáy thấp dần)" if highs.iloc[-1]<highs.iloc[0] and lows.iloc[-1]<lows.iloc[0] else "Đi ngang / hỗn hợp")
            t1,t2,t3=st.columns(3); t1.metric("Ngắn hạn · 20 phiên",trend(20)); t2.metric("Trung hạn · 60 phiên",trend(60)); t3.metric("Dài hạn · 120 phiên",trend(120))
            if main_data.symbol.nunique()>1:
                st.markdown("#### Tương quan lợi suất các mã trong file OHLCV")
                wide=main_data.pivot_table(index="date",columns="symbol",values="close").sort_index()
                corr=wide.pct_change().tail(60).corr() if len(wide)>20 else pd.DataFrame()
                if not corr.empty: st.dataframe(corr.style.format("{:.2f}"),use_container_width=True)
                else: st.info("Chưa đủ lịch sử đồng bộ để tính tương quan.")
            else: st.info("Muốn xem tương quan nhóm ngành, tải OHLCV nhiều mã cùng ngành trong file chính.")


with main_tabs[0]:

    inner_tabs = st.tabs(['Quant Lab & Backtest', 'Dữ liệu & kiểm toán', 'Phân tích doanh nghiệp'])

    # TAB 4
    with inner_tabs[0]:
        st.subheader("Quant Lab & Backtesting")
        if data is None: st.info("Cần dữ liệu OHLCV ở Sidebar.")
        else:
            h=hurst_rs(data.LOG_RETURN); ent=return_entropy(data.LOG_RETURN)
            gk=annualized_gk(data); park=annualized_parkinson(data); last=data.iloc[-1]
            c1,c2,c3,c4=st.columns(4); c1.metric("Hurst R/S",fmt(h,3)); c2.metric("Entropy chuẩn hóa",fmt(ent,3)); c3.metric("Garman–Klass ann.",fmt(gk)+"%" if gk is not None else "Chưa đủ dữ liệu"); c4.metric("Parkinson ann.",fmt(park)+"%" if park is not None else "Chưa đủ dữ liệu")
            st.caption("Hurst và Entropy là ước lượng thống kê trên chuỗi lợi suất; độ nhạy cao với độ dài mẫu và không dự báo chắc chắn trạng thái tương lai.")
            st.markdown("#### Máy tính quản trị vốn")
            entry_ref=float(last.close)
            stop_input=float(stop_assumption) if stop_assumption>0 else None
            if nav>0 and stop_input is not None and stop_input<entry_ref:
                calc=calculate_position_size(nav,entry_ref,stop_input,risk_pct,max_alloc,int(lot))
                q1,q2,q3=st.columns(3); q1.metric("Khối lượng tối đa",f"{calc['quantity']:,} cp"); q2.metric("Giá trị vị thế",f"{calc['position_value']:,.0f} VND"); q3.metric("Rủi ro ước tính",f"{calc['risk_amount']:,.0f} VND")
            else: st.info("Nhập giá dừng lỗ thấp hơn giá hiện tại ở Sidebar để tính khối lượng. Không tự suy diễn khi thiếu đầu vào.")
            st.markdown("#### Backtest chiến lược mẫu")
            if st.button("CHẠY BACKTEST",type="primary",key="run_backtest"):
                bt=simple_swing_backtest(raw.copy(),fee_pct=fee,slippage_pct=slip,tax_pct=tax_pct,initial_capital=float(nav or 1))
                st.session_state["last_backtest_v3"]={k:v for k,v in bt.items() if k!="equity_curve"}
                st.session_state["last_backtest_curve_v3"]=bt.get("equity_curve")
            bt=st.session_state.get("last_backtest_v3")
            if bt:
                if "error" in bt: st.warning(bt["error"])
                else:
                    trades=bt.get("closed_trades",0); k=st.columns(5)
                    k[0].metric("Tổng lợi nhuận",fmt(bt.get("total_return_pct"))+"%")
                    k[1].metric("Số lệnh đóng",str(trades))
                    k[2].metric("Tỷ lệ thắng",fmt(bt.get("win_rate_pct"))+"%" if bt.get("win_rate_pct") is not None else "Chưa có giao dịch")
                    k[3].metric("Max Drawdown",fmt(bt.get("max_drawdown_pct"))+"%")
                    k[4].metric("Profit Factor",fmt(bt.get("profit_factor")))
                    extra=st.columns(3)
                    extra[0].metric("CAGR",fmt(bt.get("cagr_pct"))+"%" if bt.get("cagr_pct") is not None else "Chưa đủ dữ liệu")
                    extra[1].metric("Sharpe",fmt(bt.get("sharpe"),3))
                    extra[2].metric("Expectancy",fmt(bt.get("expectancy_pct"))+"%" if bt.get("expectancy_pct") is not None else "Chưa có giao dịch")
                    curve=st.session_state.get("last_backtest_curve_v3")
                    if curve is not None and len(curve)>0: st.line_chart(pd.DataFrame({"Vốn mô phỏng":list(curve)}))
                    with st.expander("Chi tiết và giả định Backtest"):
                        detail = pd.DataFrame([{"Chỉ tiêu": k, "Giá trị": str(v)} for k, v in bt.items() if k != "equity_curve"])
                        st.dataframe(detail, use_container_width=True, hide_index=True)
                        st.caption("Không có giao dịch đóng thì Win rate, Profit Factor và Expectancy không có ý nghĩa; không diễn giải thành 0%.")
            else: st.caption("Chưa chạy Backtest trong phiên làm việc này.")


    # TAB 5
    with inner_tabs[1]:
        st.subheader("Dữ liệu thô & kiểm toán chất lượng")
        if data is None: st.info("Tải OHLCV ở Sidebar để xem dữ liệu và kiểm toán.")
        else:
            quality=assess_data_quality(main_data)
            q1,q2,q3,q4=st.columns(4); q1.metric("Điểm chất lượng",f"{quality.get('score','—')}/100"); q2.metric("Trạng thái",quality.get("status","—")); q3.metric("Số dòng",f"{len(main_data):,}"); q4.metric("Số mã",str(main_data.symbol.nunique()))
            for issue in quality.get("issues",[]): st.warning(issue)
            flags=audit_flags(data)
            if flags:
                for f in flags: st.warning(f)
            else: st.success("Chưa phát hiện bất thường cơ bản theo các quy tắc kiểm tra hiện tại.")
            st.markdown("#### OHLCV và các cột kiểm toán")
            st.dataframe(data,use_container_width=True,hide_index=True)
            csv=data.to_csv(index=False).encode("utf-8-sig")
            xlsx_buf=io.BytesIO()
            with pd.ExcelWriter(xlsx_buf,engine="openpyxl") as writer: data.to_excel(writer,index=False,sheet_name="OHLCV_Audit")
            json_bytes=data.to_json(orient="records",date_format="iso",force_ascii=False,indent=2).encode("utf-8")
            d1,d2,d3=st.columns(3)
            d1.download_button("TẢI CSV",csv,file_name=f"{selected_symbol}_audit.csv",mime="text/csv")
            d2.download_button("TẢI EXCEL",xlsx_buf.getvalue(),file_name=f"{selected_symbol}_audit.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            d3.download_button("TẢI JSON",json_bytes,file_name=f"{selected_symbol}_audit.json",mime="application/json")
            with st.expander("Kiểm toán dữ liệu gốc và giới hạn"):
                st.write("Cột gốc được giữ: date, symbol, open, high, low, close, volume.")
                st.write("Cột tính thêm: LOG_RETURN, CLV, VOLUME_ZSCORE, TURNOVER, ILLIQUIDITY_AMIHUD và các chỉ báo kỹ thuật.")
                st.write("Phát hiện biến động giá lớn chỉ tạo cảnh báo kiểm tra điều chỉnh giá; không thể xác định chắc chắn cổ tức/chia tách nếu không có dữ liệu sự kiện doanh nghiệp.")


    # TAB 6 — INVESTMENT INTELLIGENCE
    with inner_tabs[2]:
        st.subheader("Báo cáo phân tích đầu tư tổng hợp")
        st.caption("Báo cáo kết hợp dữ liệu giá ở các tab trước với thông tin doanh nghiệp và tài chính do người dùng nhập. Không tự truy cập dữ liệu doanh nghiệp hoặc tự tạo số liệu.")

        with st.expander("A. Thông tin doanh nghiệp & dữ liệu tài chính", expanded=True):
            c1,c2=st.columns(2)
            with c1:
                business_model=st.text_area("Mô hình kinh doanh / lĩnh vực cốt lõi", key="inv_business_model", height=85, placeholder="Nhập ngành nghề, sản phẩm/dịch vụ và nguồn doanh thu chính...")
                growth_drivers=st.text_area("Động lực tăng trưởng", key="inv_growth_drivers", height=85, placeholder="Ví dụ: thị trường, đơn hàng, công suất, sản phẩm mới...")
                company_events=st.text_area("Tin tức / sự kiện doanh nghiệp (kèm ngày và nguồn)", key="inv_events", height=85)
            with c2:
                business_risks=st.text_area("Rủi ro đặc thù doanh nghiệp/ngành", key="inv_business_risks", height=85)
                foreign_flow=st.text_area("Giao dịch khối ngoại / tự doanh (nếu có số liệu và kỳ thống kê)", key="inv_foreign_flow", height=85)
                data_period=st.text_input("Kỳ báo cáo tài chính", key="inv_period", placeholder="Ví dụ: Q3/2026 hoặc 9T/2026")
            st.markdown("**Chỉ tiêu tài chính – nhập đúng đơn vị ghi trên báo cáo**")
            f1,f2,f3,f4=st.columns(4)
            with f1: revenue=float(st.number_input("Doanh thu kỳ báo cáo", min_value=0.0, value=0.0, key="inv_revenue"))
            with f2: revenue_growth=float(st.number_input("Tăng trưởng doanh thu (%)", value=0.0, key="inv_revenue_growth"))
            with f3: net_profit=float(st.number_input("LNST kỳ báo cáo", min_value=0.0, value=0.0, key="inv_net_profit"))
            with f4: profit_growth=float(st.number_input("Tăng trưởng LNST (%)", value=0.0, key="inv_profit_growth"))
            vcol1,vcol2,vcol3=st.columns(3)
            with vcol1: market_cap=float(st.number_input("Vốn hóa (VND)",min_value=0.0,value=0.0,key="inv_market_cap"))
            with vcol2:
                net_debt=float(st.number_input("Nợ ròng (VND)",value=0.0,key="inv_net_debt"))
                net_debt_confirmed=st.checkbox("Đã xác nhận số liệu nợ ròng",value=False,key="inv_net_debt_confirmed")
            with vcol3: ebitda=float(st.number_input("EBITDA (VND)",min_value=0.0,value=0.0,key="inv_ebitda"))
            pcol1,pcol2=st.columns(2)
            with pcol1: industry_pe=float(st.number_input("P/E tham chiếu ngành (lần)",min_value=0.0,value=0.0,key="inv_industry_pe"))
            with pcol2: industry_pb=float(st.number_input("P/B tham chiếu ngành (lần)",min_value=0.0,value=0.0,key="inv_industry_pb"))
            g1,g2,g3,g4=st.columns(4)
            with g1: eps=float(st.number_input("EPS (đồng/cp)", min_value=0.0, value=0.0, key="inv_eps"))
            with g2: bvps=float(st.number_input("BVPS (đồng/cp)", min_value=0.0, value=0.0, key="inv_bvps"))
            with g3: roe=float(st.number_input("ROE (%)", value=0.0, key="inv_roe"))
            with g4: roa=float(st.number_input("ROA (%)", value=0.0, key="inv_roa"))
            h1,h2,h3,h4=st.columns(4)
            with h1: gross_margin=float(st.number_input("Biên lợi nhuận gộp (%)", value=0.0, key="inv_gross_margin"))
            with h2: net_margin=float(st.number_input("Biên LNST (%)", value=0.0, key="inv_net_margin"))
            with h3: debt_ratio=float(st.number_input("Nợ/Vốn chủ (%)", value=0.0, key="inv_debt_ratio"))
            with h4: cfo=float(st.number_input("Dòng tiền HĐKD", value=0.0, key="inv_cfo"))
            st.caption("Giá trị 0 được xem là chưa nhập. Hãy thống nhất đơn vị tiền tệ giữa các kỳ khi so sánh.")

        if data is None:
            st.warning("Chưa có dữ liệu OHLCV. Hãy tải dữ liệu ở Sidebar để tạo phần phân tích xu hướng và vùng giá.")
        else:
            last=data.iloc[-1]
            current_price=float(last.close)
            sr6=find_support_resistance(data)
            support6=sr6.get("support"); resistance6=sr6.get("resistance")
            atr6=last.get("ATR14")
            trend20="Tăng" if len(data)>=20 and data.close.iloc[-1]>data.close.iloc[-20] else ("Giảm" if len(data)>=20 else "Chưa đủ dữ liệu")
            trend60="Tăng" if len(data)>=60 and data.close.iloc[-1]>data.close.iloc[-60] else ("Giảm" if len(data)>=60 else "Chưa đủ dữ liệu")
            rsi6=last.get("RSI14")
            valuation=valuation_metrics(current_price,eps,bvps,net_debt if net_debt_confirmed else None,ebitda,market_cap)
            pe=valuation.get("pe")
            pb=valuation.get("pb")
            ev_ebitda=valuation.get("ev_ebitda")
            fundamental_flags=quality_flags(revenue_growth,profit_growth,roe,cfo,net_profit,debt_ratio)
            pnl6=((current_price/entry)-1)*100 if entry>0 and qty>0 else None
            st.markdown("### PHÂN TÍCH ĐẦU TƯ CỔ PHIẾU " + str(selected_symbol))
            st.caption(f"Giá đóng cửa mới nhất trong file: {current_price:,.0f} · Ngày dữ liệu: {pd.to_datetime(last.date).date()} · Kỳ BCTC khai báo: {data_period or 'Chưa có dữ liệu'}")
            completeness=sum([bool(business_model.strip()),bool(growth_drivers.strip()),revenue>0,net_profit>0,eps>0,roe!=0,bvps>0,bool(business_risks.strip())])
            st.metric("Mức độ đầy đủ dữ liệu đầu vào",f"{completeness}/8 nhóm thông tin")

            report=[]
            report.append(f"PHÂN TÍCH ĐẦU TƯ CỔ PHIẾU {selected_symbol} — cập nhật theo dữ liệu tải lên")
            report.append(f"Giá tham chiếu: {current_price:,.0f} đồng/cp | Ngày dữ liệu: {pd.to_datetime(last.date).date()} | Kỳ BCTC: {data_period or 'Chưa có dữ liệu'}")
            report.append("\n1. TỔNG QUAN & NỘI TẠI DOANH NGHIỆP")
            report.append("Mô hình kinh doanh: "+(business_model.strip() or "Chưa có dữ liệu doanh nghiệp."))
            report.append("Động lực tăng trưởng: "+(growth_drivers.strip() or "Chưa có dữ liệu để xác định động lực tăng trưởng."))
            report.append(f"Doanh thu: {revenue:,.2f}" if revenue>0 else "Doanh thu: Chưa có dữ liệu.")
            report.append(f"Tăng trưởng doanh thu: {revenue_growth:.2f}%" if revenue_growth!=0 else "Tăng trưởng doanh thu: Chưa có dữ liệu.")
            report.append(f"LNST: {net_profit:,.2f}" if net_profit>0 else "LNST: Chưa có dữ liệu.")
            report.append(f"Tăng trưởng LNST: {profit_growth:.2f}%" if profit_growth!=0 else "Tăng trưởng LNST: Chưa có dữ liệu.")
            report.append(f"EPS: {eps:,.0f} | ROE: {roe:.2f}% | ROA: {roa:.2f}%" if eps>0 or roe!=0 or roa!=0 else "EPS/ROE/ROA: Chưa có dữ liệu.")
            report.append(f"Biên gộp: {gross_margin:.2f}% | Biên LNST: {net_margin:.2f}% | Nợ/VCSH: {debt_ratio:.2f}% | CFO: {cfo:,.2f}" if any([gross_margin!=0,net_margin!=0,debt_ratio!=0,cfo!=0]) else "Biên lợi nhuận, đòn bẩy và dòng tiền HĐKD: Chưa có dữ liệu.")
            report.append("\n2. ĐỊNH GIÁ & RỦI RO")
            report.append(f"P/E tính từ giá đóng cửa và EPS nhập vào: {pe:.2f} lần" if pe is not None else "P/E: Chưa đủ dữ liệu EPS dương.")
            report.append(f"P/B tính từ giá đóng cửa và BVPS nhập vào: {pb:.2f} lần" if pb is not None else "P/B: Chưa đủ dữ liệu BVPS dương.")
            report.append(f"EV/EBITDA tham chiếu: {ev_ebitda:.2f} lần" if ev_ebitda is not None else "EV/EBITDA: Chưa đủ vốn hóa, nợ ròng và EBITDA dương cùng đơn vị.")
            report.append(f"So sánh P/E ngành do người dùng nhập: {industry_pe:.2f} lần" if industry_pe>0 else "P/E ngành: Chưa có dữ liệu đối chiếu.")
            report.append(f"So sánh P/B ngành do người dùng nhập: {industry_pb:.2f} lần" if industry_pb>0 else "P/B ngành: Chưa có dữ liệu đối chiếu.")
            report.append("Không kết luận cổ phiếu đắt/rẻ chỉ từ một hệ số đơn lẻ; cần cùng ngành, cùng kỳ và cùng phương pháp.")
            report.extend(["Cờ chất lượng tài chính: "+flag for flag in fundamental_flags])
            report.append("Dòng vốn ngoại/tự doanh: "+(foreign_flow.strip() or "Chưa có dữ liệu."))
            report.append("Rủi ro doanh nghiệp/ngành: "+(business_risks.strip() or "Chưa có dữ liệu rủi ro đặc thù."))
            report.append("Tin tức/sự kiện: "+(company_events.strip() or "Chưa có dữ liệu sự kiện kèm nguồn."))
            report.append("\n3. KỊCH BẢN NGẮN HẠN (THAM CHIẾU T+)")
            report.append(f"Xu hướng giá 20 phiên: {trend20}; 60 phiên: {trend60}; RSI14: {fmt(rsi6,1)}.")
            report.append(f"Hỗ trợ tham chiếu: {fmt(support6,0)}; kháng cự tham chiếu: {fmt(resistance6,0)}; ATR14: {fmt(atr6,0)}.")
            report.append("Kịch bản tích cực chỉ được xem xét khi giá xác nhận vượt kháng cự với thanh khoản phù hợp; nếu giá suy yếu dưới hỗ trợ, luận điểm ngắn hạn cần được đánh giá lại. Không mua đuổi chỉ dựa trên một chỉ báo.")
            report.append("\n4. KỊCH BẢN CHO NGƯỜI ĐANG NẮM GIỮ")
            if pnl6 is not None:
                report.append(f"Với số lượng/giá vốn đã nhập: lãi/lỗ tạm tính {pnl6:+.2f}%, chưa tính phí và thuế.")
            else:
                report.append("Chưa đủ thông tin vị thế (cần đồng thời có số lượng và giá vốn) để tính lãi/lỗ.")
            report.append("Đánh giá duy trì/giảm tỷ trọng cần kết hợp tỷ trọng danh mục, mức chịu rủi ro, luận điểm cơ bản và mức vô hiệu; dữ liệu tỷ trọng danh mục hiện chưa đầy đủ nếu không nhập NAV/vị thế.")
            report.append("\n5. KỊCH BẢN CHO NGƯỜI QUAN SÁT / ĐẦU TƯ TRUNG–DÀI HẠN")
            report.append("Có thể xây dựng các kịch bản giải ngân theo giai đoạn sau khi đối chiếu định giá, chất lượng lợi nhuận, dòng tiền và xu hướng dài hạn. Ứng dụng không tự đưa tỷ lệ phân bổ vốn cố định khi chưa có hồ sơ rủi ro và định giá mục tiêu.")
            report.append("\n6. KẾT LUẬN & ĐIỀU KIỆN CẦN THEO DÕI")
            report.append("Kết luận hiện tại: "+("Dữ liệu kỹ thuật có xu hướng tích cực nhưng dữ liệu cơ bản còn thiếu; chỉ nên xem là đánh giá sơ bộ." if trend20=="Tăng" and completeness<6 else ("Xu hướng kỹ thuật chưa tích cực hoặc chưa đủ dữ liệu; cần chờ thêm xác nhận." if trend20!="Tăng" else "Đã có một phần dữ liệu cơ bản và kỹ thuật; cần kiểm tra chéo báo cáo gốc trước khi kết luận.")))
            report.append("Các điều kiện làm thay đổi đánh giá: báo cáo tài chính mới, thay đổi triển vọng/đơn hàng, dòng tiền kinh doanh, biến động nợ, sự kiện doanh nghiệp và việc giá phá vỡ các vùng kỹ thuật tham chiếu.")
            report.append("\nLƯU Ý: Báo cáo là công cụ nghiên cứu/giáo dục dựa trên dữ liệu do người dùng cung cấp, không phải khuyến nghị đầu tư cá nhân hay cam kết lợi nhuận. Các chỉ tiêu tài chính cần đối chiếu báo cáo gốc và nguồn công bố chính thức.")

            with st.expander("XEM BÁO CÁO PHÂN TÍCH ĐẦY ĐỦ", expanded=True):
                st.markdown("#### 1. Tổng quan & nội tại doanh nghiệp")
                st.write("**Mô hình kinh doanh:**",business_model or "Chưa có dữ liệu.")
                st.write("**Động lực tăng trưởng:**",growth_drivers or "Chưa có dữ liệu.")
                fin_rows=[("Doanh thu",fmt(revenue)),("Tăng trưởng doanh thu",fmt(revenue_growth)+"%" if revenue_growth!=0 else "Chưa có dữ liệu"),("LNST",fmt(net_profit)),("Tăng trưởng LNST",fmt(profit_growth)+"%" if profit_growth!=0 else "Chưa có dữ liệu"),("EPS",fmt(eps,0)),("ROE",fmt(roe)+"%" if roe!=0 else "Chưa có dữ liệu"),("ROA",fmt(roa)+"%" if roa!=0 else "Chưa có dữ liệu"),("Biên gộp",fmt(gross_margin)+"%" if gross_margin!=0 else "Chưa có dữ liệu"),("Biên LNST",fmt(net_margin)+"%" if net_margin!=0 else "Chưa có dữ liệu"),("Nợ/VCSH",fmt(debt_ratio)+"%" if debt_ratio!=0 else "Chưa có dữ liệu"),("CFO",fmt(cfo))]
                st.dataframe(pd.DataFrame(fin_rows,columns=["Chỉ tiêu","Giá trị"]),use_container_width=True,hide_index=True)
                st.markdown("#### 2. Định giá & rủi ro")
                for flag in fundamental_flags: st.warning(flag)
                v1,v2,v3=st.columns(3); v1.metric("P/E tham chiếu",fmt(pe,2)+" lần" if pe is not None else "Chưa đủ dữ liệu"); v2.metric("P/B tham chiếu",fmt(pb,2)+" lần" if pb is not None else "Chưa đủ dữ liệu"); v3.metric("EV/EBITDA",fmt(ev_ebitda,2)+" lần" if ev_ebitda is not None else "Chưa đủ dữ liệu")
                st.caption(f"So sánh thủ công với ngành: P/E {fmt(industry_pe)} lần · P/B {fmt(industry_pb)} lần. Chỉ có giá trị khi cùng phương pháp và kỳ báo cáo.")
                st.write("**Rủi ro:**",business_risks or "Chưa có dữ liệu.")
                st.write("**Dòng vốn:**",foreign_flow or "Chưa có dữ liệu.")
                st.write("**Sự kiện:**",company_events or "Chưa có dữ liệu.")
                st.markdown("#### 3. Kịch bản ngắn hạn")
                st.write(f"Xu hướng 20 phiên: **{trend20}** · 60 phiên: **{trend60}** · RSI14: **{fmt(rsi6,1)}**")
                st.write(f"Hỗ trợ: **{fmt(support6,0)}** · Kháng cự: **{fmt(resistance6,0)}** · ATR14: **{fmt(atr6,0)}**")
                st.info("Kịch bản tham chiếu, không phải tín hiệu mua/bán tự động. Cần xác nhận giá, khối lượng, bối cảnh thị trường và mức rủi ro trước mọi quyết định.")
                st.markdown("#### 4–6. Người đang nắm giữ, người quan sát và kết luận")
                st.write(f"Lãi/lỗ vị thế đã nhập: {pnl6:+.2f}%" if pnl6 is not None else "Lãi/lỗ vị thế: Chưa đủ dữ liệu.")
                st.write("**Kết luận:**",report[-3].replace("Kết luận hiện tại: ",""))
                st.write("**Điều kiện theo dõi:**",report[-2])
                st.caption(report[-1])
            report_text="\n".join(report)
            st.download_button("TẢI BÁO CÁO PHÂN TÍCH (.TXT)",data=report_text.encode("utf-8-sig"),file_name=f"{selected_symbol}_investment_report.txt",mime="text/plain",key="download_investment_report")


with main_tabs[1]:

    inner_tabs = st.tabs(['Scanner đa cổ phiếu', 'Trợ lý & Knowledge Hub'])

    # TAB 7 — MULTI-STOCK SCANNER
    with inner_tabs[0]:
        st.subheader("Scanner đa cổ phiếu – xếp hạng tương đối")
        if main_data is None or main_data.empty:
            st.info("Tải file OHLCV có nhiều mã ở Sidebar để chạy Scanner.")
        else:
            investable=main_data[~main_data.symbol.astype(str).str.upper().isin(["VNINDEX","VN-INDEX","SECTOR","VNINDEX:IND"])].copy()
            if investable.empty:
                st.warning("Không tìm thấy mã cổ phiếu để quét; kiểm tra cột Symbol/Ticker.")
            else:
                universe=analyze_universe(investable,capital_vnd=float(nav),risk_pct=float(risk_pct),max_alloc_pct=float(max_alloc),lot_size=int(lot))
                scanner_market_data=main_data.copy()
                if bench_data is not None:
                    scanner_market_data=pd.concat([scanner_market_data,bench_data],ignore_index=True)
                scanned=scan_universe(universe,scanner_market_data)
                regime=assess_market_regime(scanner_market_data)
                a,b,c=st.columns(3)
                a.metric("Số mã quét",len(scanned)); b.metric("Trạng thái thị trường",regime.get("regime","—")); c.metric("Độ tin cậy regime",regime.get("confidence","—"))
                for why in regime.get("reasons",[]): st.caption(why)
                if not scanned.empty:
                    st.dataframe(scanned,use_container_width=True,hide_index=True)
                    csv_scan=scanned.to_csv(index=False).encode("utf-8-sig")
                    st.download_button("TẢI BẢNG SCANNER CSV",csv_scan,file_name="BOT_TRADER_V3_SCANNER.csv",mime="text/csv")
                    st.caption("Điểm tổng là điểm heuristic để sắp xếp nghiên cứu, không phải xác suất tăng giá hay khuyến nghị giao dịch. RS benchmark chỉ được tính khi có dữ liệu VNINDEX hoặc benchmark phù hợp.")

    st.divider()
    st.caption(f"Đơn vị giá đầu vào: {price_unit} → đã quy đổi về VND/cổ phiếu. Công cụ nghiên cứu và mô phỏng. Mọi vùng giá, cảnh báo và kết quả định lượng phụ thuộc chất lượng dữ liệu, giả định và độ dài lịch sử; không phải khuyến nghị đầu tư.")


    # TAB 8 — EXPLAINABLE TRADING ASSISTANT + LINKED KNOWLEDGE HUB
    with inner_tabs[1]:
        st.subheader("Trợ lý suy luận giao dịch & Knowledge Hub")
        st.caption("Hợp nhất dữ liệu giá, chỉ báo, thị trường, RS, đa khung, quản trị rủi ro và tài liệu người dùng nạp. Mọi kết luận đều có nguồn, điều kiện và phần còn thiếu.")
        hcol1, hcol2 = st.columns(2)
        with hcol1:
            assistant_horizon = st.selectbox("Mục tiêu phân tích", ["Swing 5–20 phiên", "Ngắn hạn 1–5 phiên", "Trung hạn 1–3 tháng"], key="assistant_horizon")
        with hcol2:
            assistant_risk_style = st.selectbox("Khẩu vị rủi ro", ["Thận trọng", "Cân bằng", "Chấp nhận biến động cao"], index=1, key="assistant_risk_style")

        st.markdown("### A. Kho tài liệu dùng chung")
        st.write("Nạp báo cáo tài chính, nghị quyết, tài liệu doanh nghiệp, ghi chú phân tích hoặc dữ liệu ngành. Tài liệu được lưu cục bộ trong SQLite; không gửi lên API AI.")
        doc_file = st.file_uploader("Chọn tài liệu để liên kết", type=["pdf","docx","xlsx","xls","csv","txt","md","json"], key="knowledge_upload")
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            doc_ticker = st.text_input("Mã cổ phiếu liên quan", value=selected_symbol or "", key="knowledge_ticker")
        with dc2:
            doc_type = st.selectbox("Loại tài liệu", ["BCTC", "Báo cáo thường niên", "Nghị quyết / công bố", "Phân tích ngành", "Ghi chú nội bộ", "Dữ liệu khác"], key="knowledge_type")
        with dc3:
            doc_period = st.text_input("Kỳ / ngày tài liệu", placeholder="Ví dụ: Q3/2026", key="knowledge_period")
        doc_source = st.text_input("Nguồn phát hành / đường dẫn tham chiếu (ghi chú)", key="knowledge_source")
        doc_source_date = st.text_input("Ngày công bố tài liệu", placeholder="YYYY-MM-DD", key="knowledge_source_date")
        if st.button("LƯU VÀO KNOWLEDGE HUB", disabled=(doc_file is None), key="index_knowledge_doc"):
            try:
                result = index_document(
                    doc_file.name, doc_file.getvalue(), ticker=doc_ticker,
                    doc_type=doc_type, period=doc_period, source_name=doc_source,
                    source_date=doc_source_date
                )
                st.success(f"Đã lập chỉ mục {result['filename']} · {result['characters']:,} ký tự · ID tài liệu {result['id']}.")
            except Exception as exc:
                st.error(f"Không thể lập chỉ mục tài liệu: {exc}")
        docs_indexed = list_documents()
        if docs_indexed:
            st.dataframe(pd.DataFrame(docs_indexed), use_container_width=True, hide_index=True)
        else:
            st.info("Knowledge Hub chưa có tài liệu. Khi chưa có tài liệu, trợ lý sẽ ghi rõ thiếu nguồn doanh nghiệp.")

        st.divider()
        st.markdown("### B. Báo cáo suy luận đa nguồn")
        if data is None:
            st.warning("Cần nạp OHLCV hợp lệ trước khi trợ lý có thể phân tích mã cổ phiếu.")
        else:
            # Recompute all linked components from the same selected symbol and current sidebar inputs.
            if shared_context is None:
                st.error(shared_context_error or "Không tạo được phiên phân tích dùng chung.")
                st.stop()
            assistant_decision = shared_context["decision_engine"]
            assistant_regime = shared_context["market_regime"]
            assistant_rs_market = shared_context["rs_market"]
            assistant_rs_sector = shared_context["rs_sector"]
            assistant_mtf = shared_context["multi_timeframe"]
            assistant_quality = shared_context["data_quality"]
            assistant_valuation = valuation_metrics(
                float(data.iloc[-1].close), eps if 'eps' in locals() else None,
                bvps if 'bvps' in locals() else None,
                net_debt if ('net_debt_confirmed' in locals() and net_debt_confirmed) else None,
                ebitda if 'ebitda' in locals() else None,
                market_cap if 'market_cap' in locals() else None
            )
            assistant_fundamentals = {
                **assistant_valuation,
                "flags": quality_flags(
                    revenue_growth if 'revenue_growth' in locals() else None,
                    profit_growth if 'profit_growth' in locals() else None,
                    roe if 'roe' in locals() else None,
                    cfo if 'cfo' in locals() else None,
                    net_profit if 'net_profit' in locals() else None,
                    debt_ratio if 'debt_ratio' in locals() else None
                )
            }
            held_pnl = ((float(data.iloc[-1].close) / float(entry) - 1) * 100) if float(entry) > 0 and int(qty) > 0 else None
            assistant_position = {"quantity": int(qty), "pnl_pct": held_pnl}
            docs_for_symbol = search_documents(
                "doanh thu lợi nhuận dòng tiền rủi ro triển vọng định giá",
                ticker=selected_symbol, limit=8
            )
            memo = build_reasoning_report(
                selected_symbol, data, decision=assistant_decision,
                regime=assistant_regime, rs_market=assistant_rs_market,
                rs_sector=assistant_rs_sector, mtf=assistant_mtf,
                fundamentals=assistant_fundamentals,
                data_quality=assistant_quality, position=assistant_position,
                documents=docs_for_symbol, horizon=assistant_horizon,
                risk_style=assistant_risk_style
            )
            master_counsel = build_master_counsel(
                selected_symbol, memo, decision=assistant_decision,
                capital_vnd=float(nav), risk_pct=float(risk_pct),
                max_allocation_pct=float(max_alloc), position=assistant_position
            )
            st.markdown("## 🧭 QUÂN SƯ ĐẦU TƯ – TRADING MASTER")
            st.markdown(f"### {master_counsel['stance']}")
            st.write(master_counsel["rationale"])
            mc1,mc2,mc3,mc4=st.columns(4)
            mc1.metric("Độ bao phủ bằng chứng", f"{master_counsel['evidence_coverage_pct']}%")
            mc2.metric("Luận cứ tích cực", master_counsel["positive_count"])
            mc3.metric("Luận cứ bất lợi", master_counsel["negative_count"])
            mc4.metric("Mâu thuẫn", master_counsel["conflict_count"])
            st.caption("Độ bao phủ chỉ phản ánh nhóm dữ liệu đã có, không phải xác suất tăng giá hay xác suất thắng.")
            with st.expander("Kiểm tra liên kết dữ liệu và điều kiện chặn", expanded=True):
                st.write("**Nhóm dữ liệu đã liên kết**")
                st.dataframe(pd.DataFrame([{"Nhóm bằng chứng": k, "Trạng thái": "Đã có" if v else "Chưa có"} for k, v in master_counsel["coverage_breakdown"].items()]), use_container_width=True, hide_index=True)
                st.write("**Điều kiện chưa đạt / cần xử lý**")
                if master_counsel["blockers"]:
                    for blocker in master_counsel["blockers"]: st.warning(blocker)
                else: st.success("Không có điều kiện chặn theo bộ quy tắc hiện tại; vẫn cần kiểm tra thủ công.")
                st.write("**Việc ưu tiên tiếp theo**")
                for item in master_counsel["priority_actions"]: st.write("• " + item)

            st.markdown("### Hỏi quân sư về mã đang phân tích")
            counsel_question = st.text_input("Ví dụ: Vì sao mã này chưa đủ điều kiện? Rủi ro lớn nhất là gì? Cần bổ sung tài liệu nào?", key="master_counsel_question")
            if st.button("PHÂN TÍCH CÂU HỎI", key="ask_master_counsel"):
                st.session_state["master_counsel_answer"] = {"symbol": selected_symbol, "result": answer_counsel_question(counsel_question, master_counsel, memo, assistant_decision)}
            saved_answer = st.session_state.get("master_counsel_answer", {})
            counsel_answer = saved_answer.get("result") if saved_answer.get("symbol") == selected_symbol else None
            if counsel_answer:
                st.info(counsel_answer.get("answer", ""))
                if counsel_answer.get("basis"):
                    st.write("**Căn cứ liên quan**")
                    for item in counsel_answer["basis"]: st.write("• " + str(item))
                st.caption(counsel_answer.get("caveat", ""))
            if st.button("LƯU BIÊN BẢN SUY LUẬN VÀO NHẬT KÝ", key="save_master_decision"):
                rid = save_decision_record(selected_symbol, master_counsel, memo,
                                           counsel_question, counsel_answer if counsel_answer else {})
                st.success(f"Đã lưu biên bản #{rid} vào nhật ký cục bộ.")
            journal = list_decision_records(limit=20)
            if journal:
                with st.expander("Nhật ký các lần đánh giá gần đây"):
                    st.dataframe(pd.DataFrame(journal), use_container_width=True, hide_index=True)

            st.markdown(f"## {memo['headline']}")
            st.caption(f"Mã: {selected_symbol} · Kỳ vọng nắm giữ: {assistant_horizon} · Khẩu vị: {assistant_risk_style} · Trạng thái: {memo['status']}")
            p1,p2,p3,p4 = st.columns(4)
            p1.metric("Bằng chứng tích cực", len(memo["positives"]))
            p2.metric("Bằng chứng tiêu cực", len(memo["negatives"]))
            p3.metric("Mâu thuẫn cần xử lý", len(memo["conflicts"]))
            p4.metric("Thông tin còn thiếu", len(memo["missing"]))

            st.markdown("#### 1. Luận cứ tích cực")
            if memo["positives"]:
                for item in memo["positives"]: st.success(item)
            else: st.write("Chưa có luận cứ tích cực đủ điều kiện.")
            st.markdown("#### 2. Rủi ro / luận cứ bất lợi")
            if memo["negatives"]:
                for item in memo["negatives"]: st.warning(item)
            else: st.write("Chưa phát hiện luận cứ bất lợi theo bộ quy tắc hiện tại; không đồng nghĩa không có rủi ro.")
            st.markdown("#### 3. Mâu thuẫn giữa các nguồn")
            if memo["conflicts"]:
                for item in memo["conflicts"]: st.info(item)
            else: st.write("Chưa phát hiện mâu thuẫn rõ từ các nguồn đã nạp.")
            st.markdown("#### 4. Kịch bản có điều kiện")
            st.dataframe(pd.DataFrame(memo["scenarios"]), use_container_width=True, hide_index=True)
            st.markdown("#### 5. Kế hoạch hành động / điều kiện vô hiệu")
            for item in memo["action_plan"]: st.write("• " + item)
            st.markdown("#### 6. Dữ liệu còn thiếu")
            if memo["missing"]:
                for item in memo["missing"]: st.caption("○ " + item)
            else: st.write("Các trường đầu vào chính đã có; vẫn cần xác minh nguồn gốc và kỳ báo cáo.")
            st.markdown("#### 7. Sổ bằng chứng có truy xuất nguồn")
            st.dataframe(pd.DataFrame(memo["facts"]), use_container_width=True, hide_index=True)
            if docs_for_symbol:
                with st.expander("Đoạn trích tài liệu liên quan (mở tài liệu gốc để xác minh)"):
                    for d in docs_for_symbol:
                        st.markdown(f"**{d['filename']}** · {d.get('doc_type','')} · {d.get('period','')} · ticker={d.get('ticker','')}")
                        st.write(d.get("excerpt",""))
                        st.caption(f"Nguồn ghi chú: {d.get('source_name') or 'Chưa khai báo'} · Điểm khớp từ khóa: {d.get('score',0)}")
            report_payload = {
                "version": "4.3.0", "symbol": selected_symbol,
                "shared_analysis": shared_context,
                "master_counsel": master_counsel,
                "generated_at": pd.Timestamp.now().isoformat(),
                "assistant_memo": memo,
                "decision_engine": assistant_decision,
                "market_regime": assistant_regime,
                "rs_market": assistant_rs_market, "rs_sector": assistant_rs_sector,
                "multi_timeframe": assistant_mtf, "data_quality": assistant_quality,
                "valuation": assistant_valuation
            }
            st.download_button(
                "TẢI HỒ SƠ SUY LUẬN JSON",
                data=json.dumps(report_payload, ensure_ascii=False, indent=2, default=str).encode("utf-8-sig"),
                file_name=f"{selected_symbol}_trading_master_dossier_v4.3.0.json",
                mime="application/json", key="download_reasoning_dossier"
            )
            st.caption(memo["disclaimer"])


with main_tabs[2]:

    inner_tabs = [st.container()]

    # TAB 9 — SWING TRADING EXPERT (BOTH: NEW OPPORTUNITIES + EXISTING POSITIONS)
    with inner_tabs[0]:
        st.subheader("CHUYÊN GIA CHIẾN LƯỢC SWING TRADING · 5–20 PHIÊN")
        st.caption("Phong cách cân bằng: vừa sàng lọc cơ hội mới, vừa quản lý vị thế đang nắm giữ. Dùng chung dữ liệu OHLCV, VN-Index, ngành, rủi ro và Knowledge Hub.")
        if data is None:
            st.warning("Nạp dữ liệu OHLCV hợp lệ ở Sidebar để sử dụng Chuyên gia Swing Trading.")
        else:
            if shared_context is None:
                st.error(shared_context_error or "Không tạo được phiên phân tích dùng chung.")
                st.stop()
            swing_regime = shared_context["market_regime"]
            swing_rs_market = shared_context["rs_market"]
            swing_rs_sector = shared_context["rs_sector"]
            swing_docs = search_documents("doanh thu lợi nhuận dòng tiền rủi ro triển vọng định giá", ticker=selected_symbol, limit=8)
            swing_is_holding = str(position_mode).startswith("🔵")
            swing_position = ({"mode": "MANAGE_EXISTING", "quantity": int(qty), "entry_price": float(entry), "stop_price": float(stop_assumption)}
                              if swing_is_holding else {"mode": "NEW_ENTRY", "quantity": 0})
            swing_report = analyze_swing_setup(
                data, market_regime=swing_regime, rs_market=swing_rs_market,
                rs_sector=swing_rs_sector, documents=swing_docs,
                capital_vnd=float(nav), risk_pct=float(risk_pct),
                max_allocation_pct=float(max_alloc), lot_size=int(lot),
                position=swing_position, risk_style="CÂN BẰNG",
                data_conflicts=audit_flags(raw),
                data_quality=shared_context["data_quality"],
                valuation={**valuation_metrics(
                    float(data.iloc[-1].close),
                    eps if 'eps' in locals() else None,
                    bvps if 'bvps' in locals() else None,
                    net_debt if ('net_debt_confirmed' in locals() and net_debt_confirmed) else None,
                    ebitda if 'ebitda' in locals() else None,
                    market_cap if 'market_cap' in locals() else None
                ),
                    "industry_pe": industry_pe if 'industry_pe' in locals() else None,
                    "industry_pb": industry_pb if 'industry_pb' in locals() else None
                },
                fundamental_flags=quality_flags(
                    revenue_growth if 'revenue_growth' in locals() else None,
                    profit_growth if 'profit_growth' in locals() else None,
                    roe if 'roe' in locals() else None,
                    cfo if 'cfo' in locals() else None,
                    net_profit if 'net_profit' in locals() else None,
                    debt_ratio if 'debt_ratio' in locals() else None
                )
            )

            swing_report["shared_analysis_id"] = shared_context["analysis_id"]
            swing_report["symbol"] = selected_symbol
            st.markdown("### A. Kết luận chiến lược cho mã đang chọn")
            sc1, sc2, sc3, sc4 = st.columns(4)
            sc1.metric("Mã", selected_symbol)
            sc2.metric("Điểm Swing", "Chưa đủ" if swing_report.get("score") is None else f"{swing_report['score']}/100")
            sc3.metric("Mô hình", swing_report.get("setup", "Chưa rõ"))
            sc4.metric("Thị trường", swing_report.get("market_gate", "Chưa rõ"))
            st.markdown("### QUYẾT ĐỊNH CỦA QUÂN SƯ")
            st.markdown(f"## {swing_report.get('conclusion', swing_report.get('status', 'CHƯA ĐỦ DỮ LIỆU'))}")
            st.caption("Nói ngắn gọn: Đứng ngoài = không mở vị thế mới; Chờ xác nhận = chưa mua; Kế hoạch giao dịch = chỉ xem xét khi điều kiện kích hoạt còn đúng. Điểm Swing là điểm sàng lọc, không phải xác suất thắng.")

            if swing_report.get("status") == "INSUFFICIENT_DATA":
                for item in swing_report.get("blockers", []): st.warning(item)
                for item in swing_report.get("reasons", []): st.write("• " + item)
            else:
                with st.expander("Luận cứ tích cực và bất lợi", expanded=True):
                    cpos, cneg = st.columns(2)
                    with cpos:
                        st.markdown("**Điểm ủng hộ**")
                        for item in swing_report["positives"]: st.success(item)
                        if not swing_report["positives"]: st.write("Chưa có luận cứ tích cực.")
                    with cneg:
                        st.markdown("**Điểm bất lợi**")
                        for item in swing_report["negatives"]: st.warning(item)
                        if not swing_report["negatives"]: st.write("Chưa phát hiện theo bộ lọc hiện tại.")
                st.markdown("### B. Hành vi giá, dòng tiền và định giá")
                behavior = swing_report.get("market_behavior", {})
                b1, b2 = st.columns(2)
                with b1:
                    st.markdown("**Dòng tiền & bẫy giá – phân tích đa phiên**")
                    flow = swing_report.get("flow_trap", {})
                    f1, f2 = st.columns(2)
                    f1.metric("Proxy dòng tiền", flow.get("flow_label", "Chưa đủ dữ liệu"))
                    f2.metric("Rủi ro bẫy giá", flow.get("trap_label", "Chưa đủ dữ liệu"))
                    fm = flow.get("metrics", {})
                    f3, f4, f5 = st.columns(3)
                    f3.metric("RVOL 20 phiên", fmt(fm.get("relative_volume_20"), 2) + "x")
                    f4.metric("Thay đổi giá 20 phiên", fmt(fm.get("price_change_20_pct"), 2) + "%")
                    f5.metric("Phiên cung mạnh / 5", str(fm.get("weak_high_volume_sessions_5", "—")))
                    st.caption("OBV/CLV-volume là proxy từ OHLCV, không phải dữ liệu lệnh mua/bán chủ động và không xác định danh tính tổ chức.")
                    for signal in flow.get("signals", behavior.get("signals", [])): st.write("• " + signal)
                    for caution in flow.get("cautions", behavior.get("cautions", [])): st.caption(caution)
                    with st.expander("Chỉ số chi tiết và sự kiện nghi vấn", expanded=False):
                        st.json(fm)
                    st.markdown("**Chẩn đoán bổ sung phiên gần nhất**")
                    st.write(behavior.get("label", "Chưa đủ dữ liệu"))
                with b2:
                    st.markdown("**Định giá theo dữ liệu đã nhập**")
                    val = swing_report.get("valuation", {})
                    st.write(f"P/E: {fmt(val.get('pe'), 2)} lần · P/B: {fmt(val.get('pb'), 2)} lần · EV/EBITDA: {fmt(val.get('ev_ebitda'), 2)} lần")
                    for flag in swing_report.get("fundamental_flags", []): st.write("• " + flag)
                    st.caption("Không kết luận rẻ/đắt nếu thiếu dữ liệu cùng kỳ và so sánh doanh nghiệp cùng ngành.")
                if swing_report.get("position", {}).get("mode") == "MANAGE_EXISTING":
                    st.markdown("### C. Kế hoạch quản lý vị thế đang nắm giữ")
                    pos = swing_report.get("position", {})
                    pc1, pc2, pc3, pc4 = st.columns(4)
                    pc1.metric("Giá vốn", fmt(pos.get("entry_price"), 0))
                    pc2.metric("Giá hiện tại", fmt(pos.get("market_price"), 0))
                    pc3.metric("Mốc vô hiệu tham chiếu", fmt(pos.get("reference_invalidation"), 0))
                    pc4.metric("Lãi/lỗ tạm tính", fmt(pos.get("pnl_pct_before_costs"), 2) + "%")
                    st.caption("Mốc bảo vệ động tham chiếu (ATR, không tự động đặt lệnh): " + fmt(pos.get("trailing_stop_reference"), 0))
                    pt1, pt2 = st.columns(2)
                    pt1.metric("Mục tiêu tham chiếu 1", fmt(pos.get("target_1_reference"), 0))
                    pt2.metric("Mục tiêu tham chiếu 2", fmt(pos.get("target_2_reference"), 0))
                    st.caption("Mục tiêu 1/2 được tính theo bội số rủi ro từ giá vốn và mốc vô hiệu. Đây là mốc nghiên cứu, không phải lệnh chốt tự động. Mốc vô hiệu dùng giá dừng lỗ người dùng nhập nếu hợp lệ; nếu không, dùng ATR và hỗ trợ gần nhất.")
                    st.info("Trạng thái vị thế: " + str(pos.get("status", "CHƯA RÕ")))
                    with st.expander("Các giai đoạn quản lý vị thế", expanded=False):
                        for stage in pos.get("management_stages", []):
                            st.markdown(f"**{stage['stage']}** · Điều kiện: {stage['condition']}\n\n{stage['action']}")
                    st.markdown("### D. Quy mô vị thế hiện có")
                    sizing = swing_report.get("sizing", {})
                    q1, q2, q3 = st.columns(3)
                    q1.metric("Số lượng đang nắm giữ", f"{int(sizing.get('quantity', 0)):,} cp")
                    q2.metric("Giá trị thị trường", f"{sizing.get('position_value', 0):,.0f} VND")
                    risk_amount = sizing.get("risk_amount")
                    q3.metric("Rủi ro tham chiếu", "Chưa tính" if risk_amount is None else f"{risk_amount:,.0f} VND")
                else:
                    st.markdown("### C. Kế hoạch mở vị thế mới")
                    plan = swing_report["plan"]
                    pc1, pc2, pc3, pc4 = st.columns(4)
                    pc1.metric("Kích hoạt tham chiếu", fmt(plan.get("reference_trigger"), 0))
                    pc2.metric("Mức vô hiệu", fmt(plan.get("invalidation"), 0))
                    pc3.metric("Mục tiêu 1", fmt(plan.get("target_1"), 0))
                    pc4.metric("Mục tiêu 2", fmt(plan.get("target_2"), 0))
                    st.write(f"R:R tham chiếu: **{fmt(plan.get('rr_target_1'), 2)} : 1** đến mục tiêu 1; **{fmt(plan.get('rr_target_2'), 2)} : 1** đến mục tiêu 2.")
                    st.write(f"ATR14: {fmt(plan.get('atr14'), 2)} · Đỉnh 20 phiên trước: {fmt(plan.get('prior_20d_high'), 0)} · Đáy 20 phiên trước: {fmt(plan.get('prior_20d_low'), 0)}")
                    st.markdown("### D. Quản trị vốn cho vị thế giả định")
                    sizing = swing_report.get("sizing", {})
                    q1, q2, q3 = st.columns(3)
                    q1.metric("Số lượng tham chiếu", f"{int(sizing.get('quantity', 0)):,} cp")
                    q2.metric("Giá trị vị thế", f"{sizing.get('position_value', 0):,.0f} VND")
                    q3.metric("Rủi ro mô phỏng", f"{sizing.get('risk_amount', 0):,.0f} VND")
                    st.caption(f"Ngân sách rủi ro: {sizing.get('risk_budget', 0):,.0f} VND · Trạng thái sizing: {sizing.get('status', 'N/A')}. Nếu số lượng bằng 0, hệ thống khóa kế hoạch giao dịch và nêu nguyên nhân ở mục điều kiện chặn.")

                st.markdown("### F. Điều kiện chặn và việc cần làm")
                if swing_report.get("blockers"):
                    for item in swing_report["blockers"]: st.warning(item)
                else:
                    st.success("Không có điều kiện chặn theo bộ lọc hiện tại; vẫn cần xác minh dữ liệu và kế hoạch.")
                for item in swing_report.get("next_steps", []): st.write("• " + item)
                with st.expander("Bằng chứng đầu vào đã liên kết", expanded=False):
                    st.json(swing_report.get("evidence", {}))
                    if swing_docs:
                        for doc in swing_docs:
                            st.markdown(f"**{doc.get('filename')}** · {doc.get('doc_type','')} · {doc.get('period','')}")
                            st.write(doc.get("excerpt", ""))
                    else:
                        st.info("Chưa có tài liệu doanh nghiệp gắn với mã này trong Knowledge Hub.")
                st.download_button(
                    "TẢI BÁO CÁO SWING JSON",
                    data=json.dumps(swing_report, ensure_ascii=False, indent=2, default=str).encode("utf-8-sig"),
                    file_name=f"{selected_symbol}_swing_master_5-20_sessions.json",
                    mime="application/json", key="download_swing_expert_report"
                )

            st.divider()
            st.markdown("### G. Sàng lọc cơ hội mới trên toàn bộ danh sách mã")
            st.caption("Scanner xếp hạng để nghiên cứu thêm; không tự động tạo lệnh. Các mã thiếu 50 phiên hoặc dữ liệu chỉ báo không hợp lệ sẽ bị loại khỏi bảng.")
            if st.button("CHẠY SWING SCANNER", key="run_swing_expert_scanner"):
                st.session_state["swing_scanner_result"] = scan_swing_universe(
                    main_data, market_regime=swing_regime, capital_vnd=float(nav),
                    risk_pct=float(risk_pct), max_allocation_pct=float(max_alloc),
                    lot_size=int(lot), risk_style="CÂN BẰNG"
                )
            swing_scan = st.session_state.get("swing_scanner_result")
            if isinstance(swing_scan, pd.DataFrame) and not swing_scan.empty:
                st.dataframe(swing_scan, use_container_width=True, hide_index=True)
                st.download_button("TẢI KẾT QUẢ SWING SCANNER CSV", swing_scan.to_csv(index=False).encode("utf-8-sig"),
                                   file_name="swing_trading_scanner_5-20_sessions.csv", mime="text/csv", key="download_swing_scanner_csv")
            elif isinstance(swing_scan, pd.DataFrame):
                st.info("Không có mã nào đủ điều kiện dữ liệu để đưa vào bảng sàng lọc.")
            st.caption("Phân hệ Swing 5–20 phiên dùng bộ quy tắc giải thích được. Chưa được kiểm định walk-forward riêng; mọi mức giá là tham chiếu nghiên cứu, không phải khuyến nghị đầu tư cá nhân.")

