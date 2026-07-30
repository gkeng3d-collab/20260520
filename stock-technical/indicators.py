"""คำนวณ technical indicators ด้วย pandas ล้วน (ไม่ต้องติดตั้ง TA-Lib)"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class IndicatorConfig:
    sma_windows: list = field(default_factory=lambda: [20, 50, 200])
    ema_windows: list = field(default_factory=list)
    bollinger: bool = True
    bb_window: int = 20
    bb_std: float = 2.0
    rsi: bool = True
    rsi_period: int = 14
    macd: bool = True
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    volume: bool = True


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window, min_periods=window).mean()


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False, min_periods=span).mean()


def bollinger(series: pd.Series, window: int = 20, num_std: float = 2.0):
    mid = sma(series, window)
    sd = series.rolling(window, min_periods=window).std(ddof=0)
    return mid, mid + num_std * sd, mid - num_std * sd


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """RSI แบบ Wilder smoothing"""
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss
    out = 100.0 - 100.0 / (1.0 + rs)
    # ราคาไม่ขยับเลยทั้งช่วง → RS เป็น 0/0 ให้ถือเป็นกลาง
    out = out.where(~((avg_loss == 0) & (avg_gain == 0)), 50.0)
    return out


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    return macd_line, signal_line, macd_line - signal_line


def compute_all(df: pd.DataFrame, cfg: IndicatorConfig) -> pd.DataFrame:
    """คืน DataFrame ใหม่ที่เพิ่มคอลัมน์ indicator ตาม config"""
    out = df.copy()
    close = out["Close"]
    for w in cfg.sma_windows:
        out[f"SMA{w}"] = sma(close, w)
    for w in cfg.ema_windows:
        out[f"EMA{w}"] = ema(close, w)
    if cfg.bollinger:
        out["BB_MID"], out["BB_UP"], out["BB_LOW"] = bollinger(close, cfg.bb_window, cfg.bb_std)
    if cfg.rsi:
        out["RSI"] = rsi(close, cfg.rsi_period)
    if cfg.macd:
        out["MACD"], out["MACD_SIGNAL"], out["MACD_HIST"] = macd(
            close, cfg.macd_fast, cfg.macd_slow, cfg.macd_signal
        )
    return out


BULL = "🟢"
BEAR = "🔴"
FLAT = "⚪"


def _crossed_recently(a: pd.Series, b: pd.Series, bars: int) -> str | None:
    """ตรวจว่า a ตัด b ขึ้น/ลงภายใน `bars` แท่งล่าสุดหรือไม่ ('up' / 'down' / None)"""
    diff = (a - b).dropna()
    if len(diff) < 2:
        return None
    tail = np.sign(diff.iloc[-(bars + 1):])
    changes = tail.diff().dropna()
    if (changes > 0).any() and tail.iloc[-1] > 0:
        return "up"
    if (changes < 0).any() and tail.iloc[-1] < 0:
        return "down"
    return None


def summarize_signals(df: pd.DataFrame, cfg: IndicatorConfig) -> list[dict]:
    """สรุปสัญญาณล่าสุดเป็นรายการ (ภาษาไทย) สำหรับแสดงเป็นตาราง"""
    rows = []
    last = df.iloc[-1]
    close = last["Close"]

    for w in cfg.sma_windows:
        col = f"SMA{w}"
        val = last.get(col)
        if pd.isna(val):
            rows.append({"รายการ": f"ราคา เทียบ SMA{w}", "ค่า": "—",
                         "การตีความ": f"{FLAT} ข้อมูลไม่พอ (ต้องมีอย่างน้อย {w} แท่ง)"})
            continue
        if close > val:
            interp = f"{BULL} ราคาอยู่เหนือเส้นค่าเฉลี่ย (แนวโน้มเชิงบวก)"
        else:
            interp = f"{BEAR} ราคาอยู่ใต้เส้นค่าเฉลี่ย (แนวโน้มเชิงลบ)"
        rows.append({"รายการ": f"ราคา เทียบ SMA{w}", "ค่า": f"{val:,.2f}", "การตีความ": interp})

    if 50 in cfg.sma_windows and 200 in cfg.sma_windows:
        s50, s200 = last.get("SMA50"), last.get("SMA200")
        if not (pd.isna(s50) or pd.isna(s200)):
            cross = _crossed_recently(df["SMA50"], df["SMA200"], bars=10)
            if s50 > s200:
                note = " — เพิ่งเกิด Golden Cross" if cross == "up" else ""
                interp = f"{BULL} SMA50 อยู่เหนือ SMA200 (โครงสร้างขาขึ้น){note}"
            else:
                note = " — เพิ่งเกิด Death Cross" if cross == "down" else ""
                interp = f"{BEAR} SMA50 อยู่ใต้ SMA200 (โครงสร้างขาลง){note}"
            rows.append({"รายการ": "SMA50 เทียบ SMA200", "ค่า": f"{s50:,.2f} / {s200:,.2f}",
                         "การตีความ": interp})

    if cfg.rsi and "RSI" in df:
        val = last["RSI"]
        if pd.isna(val):
            rows.append({"รายการ": f"RSI ({cfg.rsi_period})", "ค่า": "—",
                         "การตีความ": f"{FLAT} ข้อมูลไม่พอ"})
        elif val > 70:
            rows.append({"รายการ": f"RSI ({cfg.rsi_period})", "ค่า": f"{val:.1f}",
                         "การตีความ": f"{BEAR} Overbought (>70) แรงซื้อตึงตัว ระวังการย่อตัว"})
        elif val < 30:
            rows.append({"รายการ": f"RSI ({cfg.rsi_period})", "ค่า": f"{val:.1f}",
                         "การตีความ": f"{BULL} Oversold (<30) แรงขายมากเกิน อาจมีแรงซื้อกลับ"})
        else:
            rows.append({"รายการ": f"RSI ({cfg.rsi_period})", "ค่า": f"{val:.1f}",
                         "การตีความ": f"{FLAT} อยู่ในโซนปกติ (30–70)"})

    if cfg.macd and "MACD" in df:
        m, s = last["MACD"], last["MACD_SIGNAL"]
        if pd.isna(m) or pd.isna(s):
            rows.append({"รายการ": "MACD", "ค่า": "—", "การตีความ": f"{FLAT} ข้อมูลไม่พอ"})
        else:
            cross = _crossed_recently(df["MACD"], df["MACD_SIGNAL"], bars=5)
            if m > s:
                note = " — เพิ่งตัดขึ้น" if cross == "up" else ""
                interp = f"{BULL} MACD อยู่เหนือเส้น Signal (โมเมนตัมบวก){note}"
            else:
                note = " — เพิ่งตัดลง" if cross == "down" else ""
                interp = f"{BEAR} MACD อยู่ใต้เส้น Signal (โมเมนตัมลบ){note}"
            rows.append({"รายการ": f"MACD ({cfg.macd_fast},{cfg.macd_slow},{cfg.macd_signal})",
                         "ค่า": f"{m:,.3f} / {s:,.3f}", "การตีความ": interp})

    if cfg.bollinger and "BB_UP" in df:
        up, low = last["BB_UP"], last["BB_LOW"]
        if not (pd.isna(up) or pd.isna(low)) and up != low:
            pct_b = (close - low) / (up - low)
            if pct_b > 1:
                interp = f"{BEAR} ปิดเหนือกรอบบน Bollinger (ร้อนแรง ระวังการย่อตัว)"
            elif pct_b < 0:
                interp = f"{BULL} ปิดใต้กรอบล่าง Bollinger (ถูกขายหนัก อาจมีแรงซื้อกลับ)"
            else:
                interp = f"{FLAT} อยู่ในกรอบ Bollinger"
            rows.append({"รายการ": f"Bollinger %B ({cfg.bb_window},±{cfg.bb_std:g}σ)",
                         "ค่า": f"{pct_b:.2f}", "การตีความ": interp})

    if cfg.volume and "Volume" in df and df["Volume"].tail(20).sum() > 0:
        avg20 = df["Volume"].tail(20).mean()
        v = last["Volume"]
        if avg20 > 0:
            ratio = v / avg20
            rows.append({"รายการ": "Volume เทียบเฉลี่ย 20 แท่ง", "ค่า": f"{ratio:.2f} เท่า",
                         "การตีความ": f"{FLAT} ปริมาณซื้อขาย{'หนาแน่นกว่า' if ratio >= 1 else 'เบาบางกว่า'}ค่าเฉลี่ย"})

    return rows
