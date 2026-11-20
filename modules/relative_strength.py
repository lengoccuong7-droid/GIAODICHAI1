from __future__ import annotations
import pandas as pd

def relative_strength(frame: pd.DataFrame, benchmark: pd.DataFrame|None=None, lookback: int=20) -> dict:
    x=frame.sort_values("date").drop_duplicates("date", keep="last")
    if len(x)<lookback+1: return {"return_pct":None,"relative_return_pct":None,"rank_score":None,"benchmark_return_pct":None}
    start_date=x.date.iloc[-lookback-1]; end_date=x.date.iloc[-1]
    ret=(float(x.close.iloc[-1])/float(x.close.iloc[-lookback-1])-1)*100
    br=None
    if benchmark is not None and not benchmark.empty:
        b=benchmark.sort_values("date").drop_duplicates("date",keep="last").set_index("date")
        # Compare both instruments over the same calendar endpoints; do not compare mismatched windows.
        if start_date in b.index and end_date in b.index and float(b.loc[start_date,"close"])>0:
            br=(float(b.loc[end_date,"close"])/float(b.loc[start_date,"close"])-1)*100
        else:
            aligned=pd.merge_asof(pd.DataFrame({"date":[start_date,end_date]}).sort_values("date"),
                b[["close"]].reset_index().sort_values("date"),on="date",direction="backward")
            if len(aligned)==2 and aligned.close.notna().all() and aligned.close.iloc[0]>0:
                br=(float(aligned.close.iloc[1])/float(aligned.close.iloc[0])-1)*100
    return {"return_pct":ret,"relative_return_pct":ret-br if br is not None else None,
            "rank_score":ret-br if br is not None else ret,"benchmark_return_pct":br}
