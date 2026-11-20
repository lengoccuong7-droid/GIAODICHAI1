from __future__ import annotations
import math

def calculate_position_size(capital_vnd, entry_price, stop_price, risk_pct=1.0, max_allocation_pct=20.0, lot_size=100, price_multiplier=1.0):
    try:
        vals=[float(capital_vnd),float(entry_price),float(stop_price),float(price_multiplier),float(risk_pct),float(max_allocation_pct)]
        if not all(math.isfinite(v) for v in vals): raise ValueError
        capital,entry,stop,mult,risk_p,alloc_p=vals
        lot=int(lot_size)
        if capital<=0 or entry<=0 or stop<=0 or stop>=entry or mult<=0 or lot<=0 or risk_p<0 or alloc_p<0:
            raise ValueError
    except (TypeError,ValueError,OverflowError):
        return {"quantity":0,"risk_budget":0.0,"position_value":0.0,"risk_amount":0.0,"status":"INPUT_INVALID"}
    budget=capital*risk_p/100.0
    per_share=(entry-stop)*mult
    max_by_risk=int(budget//per_share) if per_share>0 else 0
    max_by_alloc=int((capital*alloc_p/100.0)//(entry*mult))
    qty=max(0,min(max_by_risk,max_by_alloc))
    qty=(qty//lot)*lot
    value=qty*entry*mult; risk=qty*per_share
    return {"quantity":qty,"risk_budget":budget,"position_value":value,"risk_amount":risk,
            "risk_pct_of_capital":risk/capital*100,"allocation_pct":value/capital*100,
            "max_by_risk":max_by_risk,"max_by_allocation":max_by_alloc,"status":"OK" if qty else "NO_POSITION"}
