from __future__ import annotations
import pandas as pd

PRICE_COLUMNS = ("open", "high", "low", "close")

def normalize_price_unit(frame: pd.DataFrame | None, multiplier: float = 1.0) -> pd.DataFrame | None:
    """Return a copy with OHLC converted to VND/share; volume is unchanged."""
    if frame is None:
        return None
    factor = float(multiplier)
    if not pd.notna(factor) or factor <= 0:
        raise ValueError("Hệ số quy đổi giá phải lớn hơn 0.")
    out = frame.copy()
    for col in PRICE_COLUMNS:
        if col not in out.columns:
            raise ValueError(f"Thiếu cột giá bắt buộc: {col}")
        out[col] = pd.to_numeric(out[col], errors="coerce") * factor
    out.attrs["price_unit"] = "VND/share"
    out.attrs["source_price_multiplier"] = factor
    return out
