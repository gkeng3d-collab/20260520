"""โหลดข้อมูลราคา: Yahoo Finance / ไฟล์ CSV / ข้อมูลจำลองสำหรับทดลอง"""

import io

import numpy as np
import pandas as pd

REQUIRED_COLS = ["Open", "High", "Low", "Close"]

# ชื่อคอลัมน์ที่ยอมรับในไฟล์ CSV (เทียบแบบไม่สนตัวพิมพ์)
_COL_ALIASES = {
    "date": "Date", "datetime": "Date", "time": "Date", "timestamp": "Date",
    "วันที่": "Date",
    "open": "Open", "ราคาเปิด": "Open",
    "high": "High", "ราคาสูงสุด": "High",
    "low": "Low", "ราคาต่ำสุด": "Low",
    "close": "Close", "adj close": "Close", "ราคาปิด": "Close",
    "volume": "Volume", "vol": "Volume", "ปริมาณ": "Volume",
}


def _clean_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["Close"]).sort_index()
    if "Volume" not in df:
        df["Volume"] = 0.0
    df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0.0)
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    return df[REQUIRED_COLS + ["Volume"]]


def fetch_yahoo(symbol: str, period: str, interval: str) -> pd.DataFrame:
    """ดึงข้อมูลจาก Yahoo Finance — โยน exception เมื่อเชื่อมต่อไม่ได้"""
    import yfinance as yf

    df = yf.download(symbol, period=period, interval=interval,
                     auto_adjust=True, progress=False)
    if df is None or df.empty:
        raise ValueError(f"ไม่พบข้อมูลของ '{symbol}' — ตรวจสอบสัญลักษณ์อีกครั้ง "
                         "(หุ้นไทยต้องต่อท้ายด้วย .BK เช่น PTT.BK)")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return _clean_ohlcv(df)


def parse_csv(file: "io.BytesIO | str") -> pd.DataFrame:
    """อ่านไฟล์ CSV ที่มีคอลัมน์ Date, Open, High, Low, Close[, Volume]"""
    df = pd.read_csv(file)
    df.columns = [
        _COL_ALIASES.get(str(c).strip().lower(), str(c).strip()) for c in df.columns
    ]
    missing = [c for c in ["Date"] + REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(
            "ไฟล์ CSV ขาดคอลัมน์: " + ", ".join(missing)
            + " (ต้องมี Date, Open, High, Low, Close และจะมี Volume ด้วยก็ได้)"
        )
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).set_index("Date")
    for c in REQUIRED_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return _clean_ohlcv(df)


def make_demo_data(days: int = 500, seed: int = 42) -> pd.DataFrame:
    """สร้างข้อมูลจำลอง (random walk มีช่วงขาขึ้น/ขาลง) สำหรับทดลองใช้งานโดยไม่ต้องต่อเน็ต"""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days)
    n = len(idx)

    q = n // 4
    drift = np.concatenate([
        np.full(q, 0.0009),          # ขาขึ้น
        np.full(q, -0.0012),         # ขาลง
        np.full(q, 0.0002),          # ออกข้าง
        np.full(n - 3 * q, 0.0016),  # ขาขึ้นแรง
    ])
    rets = rng.normal(drift, 0.018)
    close = 100.0 * np.exp(np.cumsum(rets))

    open_ = np.empty(n)
    open_[0] = 100.0
    open_[1:] = close[:-1] * (1 + rng.normal(0, 0.004, n - 1))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.007, n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.007, n)))
    volume = np.round(5e6 * (1 + 25 * np.abs(rets)) * rng.lognormal(0, 0.35, n))

    df = pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=idx,
    )
    df.index.name = "Date"
    return _clean_ohlcv(df)
