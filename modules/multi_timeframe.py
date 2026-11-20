from __future__ import annotations
import pandas as pd
from .indicators import add_indicators

def resample_ohlcv(frame: pd.DataFrame, rule: str) -> pd.DataFrame:
    x=frame.copy()
    x["date"]=pd.to_datetime(x["date"],errors="coerce")
    x=x.dropna(subset=["date"]).sort_values("date").set_index("date")
    aggregated=x.resample(rule).agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"})
    aggregated=aggregated.dropna(subset=["open","high","low","close"])
    out=aggregated.reset_index()
    out["symbol"]=str(frame.symbol.iloc[-1]) if "symbol" in frame and len(frame) else "UNKNOWN"
    return out[["date","symbol","open","high","low","close","volume"]]

def timeframe_snapshot(frame: pd.DataFrame) -> dict:
    result={}
    for label,rule in [("W","W-FRI"),("M","ME")]:
        try:
            x=resample_ohlcv(frame,rule)
            e=add_indicators(x)
            if len(e):
                r=e.iloc[-1]; c=r.close; m20=r.get("SMA20"); m50=r.get("SMA50")
                result[label]={"bars":len(e),"close":float(c),"sma20":None if pd.isna(m20) else float(m20),"sma50":None if pd.isna(m50) else float(m50),
                    "trend":"TĂNG" if pd.notna(m20) and pd.notna(m50) and c>m20>m50 else "GIẢM" if pd.notna(m20) and pd.notna(m50) and c<m20<m50 else "CHƯA XÁC NHẬN"}
        except Exception as exc: result[label]={"bars":0,"trend":"LỖI TÍNH TOÁN","error":str(exc)}
    return result
