from __future__ import annotations
import math

def valuation_metrics(price_vnd=None, eps_vnd=None, bvps_vnd=None, net_debt=None, ebitda=None, market_cap=None):
    def positive(x):
        try:
            v=float(x)
            return v if math.isfinite(v) and v>0 else None
        except (TypeError,ValueError): return None
    price,eps,bvps,ebitda_v,mc=map(positive,[price_vnd,eps_vnd,bvps_vnd,ebitda,market_cap])
    try:
        nd=float(net_debt)
        if not math.isfinite(nd): nd=None
    except (TypeError,ValueError): nd=None
    pe=price/eps if price and eps else None
    pb=price/bvps if price and bvps else None
    enterprise_value=(mc+nd) if mc is not None and nd is not None else None
    ev_ebitda=enterprise_value/ebitda_v if enterprise_value is not None and enterprise_value>0 and ebitda_v else None
    return {"pe":pe,"pb":pb,"ev_ebitda":ev_ebitda,
            "limitations":["P/E cần EPS cùng kỳ và nhất quán cơ sở pha loãng.","P/B cần BVPS cùng ngày/cùng đơn vị.","EV/EBITDA chỉ tính khi có vốn hóa, nợ ròng và EBITDA đồng nhất kỳ báo cáo.","Không kết luận đắt/rẻ nếu thiếu so sánh lịch sử và doanh nghiệp cùng ngành."]}

def quality_flags(revenue_growth=None, profit_growth=None, roe=None, cfo=None, net_profit=None, debt_to_equity=None):
    flags=[]
    def num(v):
        try:
            z=float(v); return z if math.isfinite(z) else None
        except (TypeError,ValueError): return None
    rg,pg,r,cfo_v,np_v,de=map(num,[revenue_growth,profit_growth,roe,cfo,net_profit,debt_to_equity])
    if all(v is None for v in [rg,pg,r,cfo_v,np_v,de]):
        return ["Chưa đủ dữ liệu tài chính để đánh giá chất lượng lợi nhuận, dòng tiền và đòn bẩy."]
    if rg is not None and pg is not None and pg<rg: flags.append("Tăng trưởng lợi nhuận thấp hơn tăng trưởng doanh thu; kiểm tra biên lợi nhuận và chi phí.")
    if cfo_v is not None and np_v is not None and np_v>0 and cfo_v<0: flags.append("CFO âm trong khi LNST dương; cần kiểm tra chất lượng lợi nhuận và vốn lưu động.")
    if de is not None and de>200: flags.append("Nợ/Vốn chủ vượt 200%; cần đánh giá đòn bẩy theo đặc thù ngành.")
    if r is not None and r<0: flags.append("ROE âm; cần phân tích nguyên nhân và tính bền vững.")
    return flags or ["Chưa phát hiện cờ cảnh báo từ các chỉ tiêu đã nhập; dữ liệu chưa được xác minh độc lập."]
