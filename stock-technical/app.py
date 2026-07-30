"""โปรแกรมแสดงกราฟเทคนิคราคาหุ้น — รันด้วย: streamlit run app.py"""

import pandas as pd
import streamlit as st

from charts import build_figure
from data_sources import fetch_yahoo, make_demo_data, parse_csv
from indicators import IndicatorConfig, compute_all, summarize_signals

st.set_page_config(page_title="Stock Technical Viewer", page_icon="📈", layout="wide")

PERIODS = {"1 เดือน": "1mo", "3 เดือน": "3mo", "6 เดือน": "6mo",
           "1 ปี": "1y", "2 ปี": "2y", "5 ปี": "5y", "ทั้งหมด": "max"}
INTERVALS = {"รายวัน": "1d", "รายสัปดาห์": "1wk", "รายเดือน": "1mo"}


@st.cache_data(ttl=300, show_spinner="กำลังดึงข้อมูลจาก Yahoo Finance…")
def cached_fetch(symbol: str, period: str, interval: str) -> pd.DataFrame:
    return fetch_yahoo(symbol, period, interval)


with st.sidebar:
    st.header("⚙️ ตั้งค่า")
    source = st.radio("แหล่งข้อมูล",
                      ["Yahoo Finance (ออนไลน์)", "ไฟล์ CSV", "ข้อมูลตัวอย่าง (Demo)"])

    symbol = period_label = interval_label = None
    uploaded = None
    if source.startswith("Yahoo"):
        symbol = st.text_input("สัญลักษณ์หุ้น", value="PTT.BK").strip().upper()
        st.caption("หุ้นไทยต่อท้าย `.BK` เช่น `PTT.BK`, `KBANK.BK`, `CPALL.BK` · "
                   "หุ้นสหรัฐ เช่น `AAPL`, `NVDA` · คริปโต เช่น `BTC-USD`")
        c1, c2 = st.columns(2)
        period_label = c1.selectbox("ช่วงเวลา", list(PERIODS), index=3)
        interval_label = c2.selectbox("ความถี่", list(INTERVALS), index=0)
    elif source.startswith("ไฟล์"):
        uploaded = st.file_uploader(
            "อัปโหลดไฟล์ CSV", type=["csv"],
            help="ต้องมีคอลัมน์ Date, Open, High, Low, Close และจะมี Volume ด้วยก็ได้",
        )

    st.divider()
    st.subheader("Indicators")
    sma_sel = st.multiselect("SMA (ค่าเฉลี่ยอย่างง่าย)", [5, 10, 20, 50, 100, 200],
                             default=[20, 50, 200], max_selections=3)
    ema_sel = st.multiselect("EMA (ค่าเฉลี่ยถ่วงน้ำหนัก)", [9, 12, 26, 50, 100, 200],
                             default=[], max_selections=2)
    show_bb = st.checkbox("Bollinger Bands", value=True)
    show_rsi = st.checkbox("RSI", value=True)
    show_macd = st.checkbox("MACD", value=True)
    show_vol = st.checkbox("Volume", value=True)

    with st.expander("พารามิเตอร์"):
        c1, c2 = st.columns(2)
        bb_window = c1.number_input("Bollinger: ช่วง", 5, 200, 20)
        bb_std = c2.number_input("Bollinger: σ", 0.5, 5.0, 2.0, step=0.5)
        rsi_period = st.number_input("RSI: ช่วง", 2, 100, 14)
        c1, c2, c3 = st.columns(3)
        macd_fast = c1.number_input("MACD เร็ว", 2, 100, 12)
        macd_slow = c2.number_input("MACD ช้า", 3, 200, 26)
        macd_sig = c3.number_input("Signal", 2, 100, 9)
        if macd_fast >= macd_slow:
            st.warning("ค่า MACD เร็ว ควรน้อยกว่าค่า MACD ช้า")

# ---------- โหลดข้อมูลตามแหล่งที่เลือก ----------
daily = True
if source.startswith("Yahoo"):
    if not symbol:
        st.info("กรอกสัญลักษณ์หุ้นในแถบด้านซ้ายเพื่อเริ่มต้น")
        st.stop()
    try:
        df = cached_fetch(symbol, PERIODS[period_label], INTERVALS[interval_label])
    except ValueError as e:
        st.error(str(e))
        st.stop()
    except Exception as e:
        st.error(f"เชื่อมต่อ Yahoo Finance ไม่สำเร็จ: {str(e)[:200]}")
        st.info("ตรวจสอบอินเทอร์เน็ต หรือทดลองใช้โหมด **ข้อมูลตัวอย่าง (Demo)** / **ไฟล์ CSV** ไปก่อน")
        st.stop()
    label = symbol
    sub = f"Yahoo Finance · {period_label} · {interval_label}"
    daily = INTERVALS[interval_label] == "1d"
elif source.startswith("ไฟล์"):
    if uploaded is None:
        st.info("อัปโหลดไฟล์ CSV ในแถบด้านซ้าย (คอลัมน์ Date, Open, High, Low, Close[, Volume])")
        st.stop()
    try:
        df = parse_csv(uploaded)
    except Exception as e:
        st.error(f"อ่านไฟล์ไม่สำเร็จ: {str(e)[:300]}")
        st.stop()
    label = uploaded.name
    sub = f"ไฟล์ CSV · {len(df):,} แถว"
    gaps = df.index.to_series().diff().dropna()
    daily = bool(len(gaps)) and gaps.median() <= pd.Timedelta(days=1.5)
else:
    df = make_demo_data()
    label = "DEMO — ข้อมูลจำลอง"
    sub = "สร้างจาก random walk เพื่อทดลองใช้งาน ไม่ใช่หุ้นจริง"

if len(df) < 2:
    st.error("ข้อมูลน้อยเกินไป (ต้องมีอย่างน้อย 2 แถว)")
    st.stop()

cfg = IndicatorConfig(
    sma_windows=sorted(sma_sel), ema_windows=sorted(ema_sel),
    bollinger=show_bb, bb_window=int(bb_window), bb_std=float(bb_std),
    rsi=show_rsi, rsi_period=int(rsi_period),
    macd=show_macd, macd_fast=int(macd_fast), macd_slow=int(macd_slow),
    macd_signal=int(macd_sig),
    volume=show_vol and df["Volume"].sum() > 0,
)
data = compute_all(df, cfg)

# ---------- ส่วนหัว + ตัวเลขสรุป ----------
st.title(f"📈 {label}")
st.caption(sub)

last, prev = data.iloc[-1], data.iloc[-2]
chg = last["Close"] - prev["Close"]
chg_pct = chg / prev["Close"] * 100 if prev["Close"] else 0.0
period_pct = (last["Close"] / data["Close"].iloc[0] - 1) * 100

m1, m2, m3, m4 = st.columns(4)
m1.metric("ราคาปิดล่าสุด", f"{last['Close']:,.2f}", f"{chg:+,.2f} ({chg_pct:+.2f}%)")
m2.metric("เปลี่ยนแปลงทั้งช่วง", f"{period_pct:+.2f}%",
          f"ตั้งแต่ {data.index[0]:%d %b %Y}", delta_color="off")
m3.metric("สูงสุด / ต่ำสุดในช่วง", f"{data['High'].max():,.2f}",
          f"ต่ำสุด {data['Low'].min():,.2f}", delta_color="off")
if cfg.rsi and pd.notna(last.get("RSI")):
    m4.metric(f"RSI ({cfg.rsi_period})", f"{last['RSI']:.1f}")
else:
    m4.metric("จำนวนแท่ง", f"{len(data):,}")

# ---------- กราฟ ----------
fig = build_figure(data, cfg, daily=daily, revision=f"{source}|{label}|{sub}")
st.plotly_chart(fig, width="stretch",
                config={"displaylogo": False,
                        "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]})

# ---------- สรุปสัญญาณ ----------
st.subheader("สรุปสัญญาณทางเทคนิค (แท่งล่าสุด)")
signals = summarize_signals(data, cfg)
if signals:
    st.dataframe(pd.DataFrame(signals), hide_index=True, width="stretch")
else:
    st.info("เปิดใช้ indicator อย่างน้อยหนึ่งตัวเพื่อดูสรุปสัญญาณ")

# ---------- ตารางข้อมูล ----------
with st.expander("ตารางข้อมูล + ดาวน์โหลด"):
    show = data.tail(250).iloc[::-1].copy()
    show.index = show.index.strftime("%Y-%m-%d")
    st.dataframe(show.round(2), width="stretch")
    st.download_button(
        "⬇️ ดาวน์โหลด CSV (รวมค่า indicator)",
        data.round(4).to_csv().encode("utf-8-sig"),
        file_name=f"{label.replace(' ', '_')}_technical.csv",
        mime="text/csv",
    )

st.caption("⚠️ เครื่องมือนี้จัดทำเพื่อการศึกษาเท่านั้น ไม่ใช่คำแนะนำในการลงทุน · "
           "ข้อมูลจาก Yahoo Finance อาจล่าช้ากว่าตลาดจริง")
