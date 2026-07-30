"""สร้างกราฟ Plotly: แท่งเทียน + เส้นค่าเฉลี่ย + Bollinger + Volume + RSI + MACD"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from indicators import IndicatorConfig

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

# แท่งขึ้น/ลงใช้สีสถานะเขียว/แดงตามธรรมเนียมกราฟหุ้น ซึ่งเป็นคู่สีที่ผู้มีภาวะตาบอดสี
# แยกได้ยาก จึงเสริมช่องทางที่ไม่ใช่สี: แท่งขึ้นเป็นแท่งกลวง แท่งลงเป็นแท่งทึบ
UP = "#0ca30c"
DOWN = "#d03b3b"
UP_SOFT = "rgba(12,163,12,0.55)"
DOWN_SOFT = "rgba(208,59,59,0.55)"

# ช่องสีเส้นตามลำดับตายตัว (ผ่าน validate_palette ทั้งชุดร่วมกับสีม่วงของ Bollinger)
LINE_SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
BB_LINE = "rgba(74,58,167,0.65)"
BB_FILL = "rgba(74,58,167,0.07)"


def build_figure(
    df: pd.DataFrame,
    cfg: IndicatorConfig,
    *,
    daily: bool = True,
    revision: str | None = None,
) -> go.Figure:
    """รับ DataFrame ที่ผ่าน indicators.compute_all แล้ว คืน Figure หลายแผงแกน x ร่วมกัน"""
    panels = ["price"]
    if cfg.volume:
        panels.append("volume")
    if cfg.rsi:
        panels.append("rsi")
    if cfg.macd:
        panels.append("macd")

    weights = {"price": 3.4, "volume": 1.0, "rsi": 1.1, "macd": 1.2}
    heights = [weights[p] for p in panels]
    heights = [h / sum(heights) for h in heights]
    row_of = {p: i + 1 for i, p in enumerate(panels)}

    fig = make_subplots(
        rows=len(panels), cols=1, shared_xaxes=True,
        vertical_spacing=0.045, row_heights=heights,
    )

    r = row_of["price"]
    if cfg.bollinger and "BB_UP" in df:
        bb_name = f"Bollinger ({cfg.bb_window},±{cfg.bb_std:g}σ)"
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_UP"], name=bb_name, legendgroup="bb",
            showlegend=False, line=dict(color=BB_LINE, width=1),
            hovertemplate="กรอบบน %{y:,.2f}<extra></extra>",
        ), row=r, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_LOW"], name=bb_name, legendgroup="bb",
            showlegend=False, line=dict(color=BB_LINE, width=1),
            fill="tonexty", fillcolor=BB_FILL,
            hovertemplate="กรอบล่าง %{y:,.2f}<extra></extra>",
        ), row=r, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_MID"], name=bb_name, legendgroup="bb",
            line=dict(color=BB_LINE, width=1, dash="dot"),
            hovertemplate="กลางกรอบ %{y:,.2f}<extra></extra>",
        ), row=r, col=1)

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name="แท่งเทียน",
        increasing=dict(line=dict(color=UP, width=1.2), fillcolor=SURFACE),
        decreasing=dict(line=dict(color=DOWN, width=1.2), fillcolor=DOWN),
    ), row=r, col=1)

    slot = 0
    for w in sorted(cfg.sma_windows):
        col = f"SMA{w}"
        if col in df and slot < len(LINE_SLOTS):
            fig.add_trace(go.Scatter(
                x=df.index, y=df[col], name=col,
                line=dict(color=LINE_SLOTS[slot], width=2),
                hovertemplate="%{y:,.2f}<extra>" + col + "</extra>",
            ), row=r, col=1)
            slot += 1
    for w in sorted(cfg.ema_windows):
        col = f"EMA{w}"
        if col in df and slot < len(LINE_SLOTS):
            fig.add_trace(go.Scatter(
                x=df.index, y=df[col], name=col,
                line=dict(color=LINE_SLOTS[slot], width=2, dash="dash"),
                hovertemplate="%{y:,.2f}<extra>" + col + "</extra>",
            ), row=r, col=1)
            slot += 1
    fig.update_yaxes(title_text="ราคา", row=r, col=1)

    if cfg.volume:
        r = row_of["volume"]
        up_day = df["Close"].diff().fillna(0) >= 0
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"], name="Volume", showlegend=False,
            marker=dict(color=[UP_SOFT if u else DOWN_SOFT for u in up_day],
                        line_width=0),
            hovertemplate="%{y:,.0f}<extra>Volume</extra>",
        ), row=r, col=1)
        fig.update_yaxes(title_text="Volume", tickformat="~s", row=r, col=1)

    if cfg.rsi and "RSI" in df:
        r = row_of["rsi"]
        fig.add_hrect(y0=30, y1=70, fillcolor="rgba(137,135,129,0.07)",
                      line_width=0, row=r, col=1)
        for level in (30, 70):
            fig.add_hline(y=level, line=dict(color=MUTED, width=1, dash="dot"),
                          row=r, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["RSI"], name="RSI", showlegend=False,
            line=dict(color=LINE_SLOTS[0], width=2),
            hovertemplate="%{y:.1f}<extra>RSI</extra>",
        ), row=r, col=1)
        fig.update_yaxes(title_text=f"RSI({cfg.rsi_period})", range=[0, 100],
                         tickvals=[30, 50, 70], row=r, col=1)

    if cfg.macd and "MACD" in df:
        r = row_of["macd"]
        fig.add_trace(go.Bar(
            x=df.index, y=df["MACD_HIST"], name="Histogram", showlegend=False,
            marker=dict(color=[UP_SOFT if v >= 0 else DOWN_SOFT
                               for v in df["MACD_HIST"].fillna(0)],
                        line_width=0),
            hovertemplate="%{y:,.3f}<extra>Histogram</extra>",
        ), row=r, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MACD"], name="MACD", showlegend=False,
            line=dict(color=LINE_SLOTS[0], width=2),
            hovertemplate="%{y:,.3f}<extra>MACD</extra>",
        ), row=r, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MACD_SIGNAL"], name="Signal", showlegend=False,
            line=dict(color=LINE_SLOTS[1], width=2),
            hovertemplate="%{y:,.3f}<extra>Signal</extra>",
        ), row=r, col=1)
        fig.update_yaxes(title_text="MACD", zeroline=True, zerolinecolor=AXIS,
                         zerolinewidth=1, row=r, col=1)

    fig.update_xaxes(
        rangeslider_visible=False, showgrid=False, showline=True,
        linecolor=AXIS, ticks="outside", tickcolor=AXIS,
        hoverformat="%d %b %Y",
    )
    if daily:
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    fig.update_yaxes(
        gridcolor=GRID, zeroline=False, showline=False, automargin=True,
        tickfont=dict(color=MUTED, size=11),
        title_font=dict(color=INK_2, size=12), title_standoff=8,
    )

    fig.update_layout(
        template="none",
        height=430 + 115 * (len(panels) - 1),
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        font=dict(family="system-ui, -apple-system, 'Segoe UI', 'Noto Sans Thai', sans-serif",
                  size=12, color=INK_2),
        legend=dict(orientation="h", x=0, y=1.0, xanchor="left", yanchor="bottom",
                    font=dict(size=12, color=INK_2)),
        margin=dict(l=10, r=10, t=42, b=10),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#ffffff", bordercolor=AXIS,
                        font=dict(size=12, color=INK)),
        bargap=0.25,
        uirevision=revision,
    )
    return fig
