#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modern Portfolio Theory (MPT) portfolio manager.

Mean-variance portfolio analysis and optimization (Markowitz):

  analyze    per-asset statistics and correlation matrix
  optimize   max-Sharpe / min-volatility / target-return portfolio
  frontier   efficient frontier table (CSV) and chart (PNG)
  rebalance  trade list that moves current holdings to target weights

Requires numpy + scipy. matplotlib is optional (only for `frontier --plot`).
See README.md (Thai) for the full guide.
"""

import argparse
import csv
import math
import sys
from datetime import datetime

try:
    import numpy as np
except ImportError:
    sys.exit("This tool needs numpy (and scipy). Install with: pip install numpy scipy")

TRADING_DAYS = 252
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y%m%d")


def die(msg):
    sys.exit(f"error: {msg}")


def warn(msg):
    print(f"note: {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _parse_date(text):
    text = text.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _parse_float(text):
    text = text.strip().replace(",", "")
    if text == "" or text.upper() in ("NA", "N/A", "NAN", "NULL", "-"):
        return None
    return float(text)


def load_prices(path, ffill=False):
    """Read a price CSV: optional date column first, then one column per asset.

    Returns (dates, names, prices) where dates may be None and prices is a
    (T, N) float array.
    """
    try:
        with open(path, newline="", encoding="utf-8-sig") as fh:
            rows = [r for r in csv.reader(fh) if any(c.strip() for c in r)]
    except OSError as exc:
        die(f"cannot read price file: {exc}")
    if len(rows) < 2:
        die(f"{path}: need a header row and at least one data row")

    header, data = rows[0], rows[1:]
    first_is_date = _parse_date(data[0][0]) is not None or header[0].strip().lower() in (
        "date", "dates", "day", "time", "วันที่")
    names = [h.strip() for h in (header[1:] if first_is_date else header)]
    if len(names) < 2:
        die("need at least 2 asset columns for portfolio work")
    if len(set(n.lower() for n in names)) != len(names):
        die("duplicate asset names in header")

    dates, prices, last = [], [], None
    for i, row in enumerate(data, start=2):
        cells = row[1:] if first_is_date else row
        if len(cells) != len(names):
            die(f"{path} line {i}: expected {len(names)} price cells, got {len(cells)}")
        if first_is_date:
            d = _parse_date(row[0])
            if d is None:
                die(f"{path} line {i}: cannot parse date {row[0]!r}")
            dates.append(d)
        try:
            vals = [_parse_float(c) for c in cells]
        except ValueError as exc:
            die(f"{path} line {i}: {exc}")
        if any(v is None for v in vals):
            if not ffill:
                die(f"{path} line {i}: missing price (use --ffill to carry the "
                    f"previous price forward)")
            if last is None:
                die(f"{path} line {i}: missing price in the first data row; "
                    f"--ffill has nothing to carry forward")
            vals = [last[j] if v is None else v for j, v in enumerate(vals)]
        if any(v <= 0 for v in vals):
            die(f"{path} line {i}: prices must be positive")
        prices.append(vals)
        last = vals

    P = np.asarray(prices, dtype=float)
    if dates and sorted(dates) != dates:
        order = np.argsort(dates)
        dates = [dates[k] for k in order]
        P = P[order]
    if len(P) < 3:
        die("need at least 3 price rows to estimate returns")
    if len(P) < 30:
        warn(f"only {len(P)} price rows; statistics will be very noisy")
    return (dates or None), names, P


def detect_ppy(dates, override=None):
    """Periods per year, from --ppy or from the median date gap."""
    if override:
        return float(override)
    if not dates:
        warn(f"no date column; assuming daily data ({TRADING_DAYS} periods/year)")
        return float(TRADING_DAYS)
    gaps = [(b - a).days for a, b in zip(dates, dates[1:]) if (b - a).days > 0]
    med = sorted(gaps)[len(gaps) // 2] if gaps else 1
    if med <= 2:
        return float(TRADING_DAYS)
    if med <= 10:
        return 52.0
    if med <= 45:
        return 12.0
    if med <= 200:
        return 4.0
    return 1.0


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def compute_stats(P, ppy):
    """Annualized mean vector and covariance matrix from simple returns."""
    R = P[1:] / P[:-1] - 1.0
    mu = R.mean(axis=0) * ppy
    cov = np.cov(R, rowvar=False, ddof=1) * ppy
    return R, mu, cov


def max_drawdown(prices):
    peak = np.maximum.accumulate(prices)
    return float(np.min(prices / peak - 1.0))


def cagr(prices, periods, ppy):
    return float((prices[-1] / prices[0]) ** (ppy / periods) - 1.0)


def portfolio_perf(w, mu, cov, rf):
    ret = float(w @ mu)
    vol = float(math.sqrt(max(w @ cov @ w, 0.0)))
    sharpe = (ret - rf) / vol if vol > 1e-12 else float("nan")
    return ret, vol, sharpe


# ---------------------------------------------------------------------------
# Optimization (scipy SLSQP)
# ---------------------------------------------------------------------------

def _minimize(objective, n, bounds, extra_constraints=()):
    try:
        from scipy.optimize import minimize
    except ImportError:
        die("scipy is required for optimization. Install with: pip install scipy")

    cons = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}, *extra_constraints]
    rng = np.random.default_rng(0)
    eq = np.full(n, 1.0 / n)
    starts = [eq] + [eq + rng.normal(0, 0.05, n) for _ in range(4)]
    best = None
    for w0 in starts:
        res = minimize(objective, w0, method="SLSQP", bounds=bounds, constraints=cons,
                       options={"maxiter": 1000, "ftol": 1e-12})
        if res.success and (best is None or res.fun < best.fun):
            best = res
    if best is None:
        return None
    w = np.clip(best.x, [b[0] for b in bounds], [b[1] for b in bounds])
    return w / w.sum()


def solve_min_vol(mu, cov, bounds):
    return _minimize(lambda w: w @ cov @ w, len(mu), bounds)


def solve_max_sharpe(mu, cov, rf, bounds):
    def neg_sharpe(w):
        vol = math.sqrt(max(w @ cov @ w, 0.0))
        return -((w @ mu - rf) / max(vol, 1e-12))
    return _minimize(neg_sharpe, len(mu), bounds)


def solve_max_return(mu, cov, bounds):
    return _minimize(lambda w: -(w @ mu), len(mu), bounds)


def solve_target_return(mu, cov, target, bounds):
    cons = ({"type": "eq", "fun": lambda w, t=target: w @ mu - t},)
    return _minimize(lambda w: w @ cov @ w, len(mu), bounds, cons)


def efficient_frontier(mu, cov, bounds, points):
    """Min-vol portfolio for each target return between GMV and max return."""
    w_gmv = solve_min_vol(mu, cov, bounds)
    w_max = solve_max_return(mu, cov, bounds)
    if w_gmv is None or w_max is None:
        die("could not locate the ends of the frontier (infeasible constraints?)")
    lo, hi = float(w_gmv @ mu), float(w_max @ mu)
    out = []
    for t in np.linspace(lo, hi, points):
        w = solve_target_return(mu, cov, t, bounds)
        if w is not None:
            out.append((t, w))
    if not out:
        die("efficient frontier optimization failed at every point")
    return out, w_gmv


def build_bounds(n, args):
    lo = args.min_weight if args.min_weight is not None else (-1.0 if args.allow_short else 0.0)
    hi = args.max_weight if args.max_weight is not None else 1.0
    if lo > hi:
        die("--min-weight is greater than --max-weight")
    if n * hi < 1.0 - 1e-9 or n * lo > 1.0 + 1e-9:
        die(f"infeasible bounds: {n} assets in [{lo}, {hi}] cannot sum to 1")
    return [(lo, hi)] * n


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def pct(x, digits=2):
    return f"{x * 100:.{digits}f}%"


def fmt_table(headers, rows):
    cols = [headers] + [[str(c) for c in row] for row in rows]
    widths = [max(len(r[i]) for r in cols) for i in range(len(headers))]
    def line(cells):
        return "  ".join(
            c.ljust(widths[i]) if i == 0 else c.rjust(widths[i]) for i, c in enumerate(cells))
    body = [line(headers), line(["-" * w for w in widths])]
    body += [line([str(c) for c in row]) for row in rows]
    return "\n".join(body)


def print_data_info(path, dates, names, P, ppy):
    span = f", {dates[0]} .. {dates[-1]}" if dates else ""
    freq = {252.0: "daily", 52.0: "weekly", 12.0: "monthly", 4.0: "quarterly",
            1.0: "yearly"}.get(ppy, f"{ppy:g}/year")
    print(f"Data: {path} | {len(names)} assets, {len(P)} rows{span} | "
          f"frequency: {freq} ({ppy:g} periods/year)\n")


def print_portfolio(title, w, names, mu, cov, rf):
    ret, vol, sharpe = portfolio_perf(w, mu, cov, rf)
    print(f"== {title} ==")
    rows = [(n, pct(x)) for n, x in sorted(zip(names, w), key=lambda p: -p[1])
            if abs(x) >= 5e-5]
    print(fmt_table(["Asset", "Weight"], rows))
    print(f"\nExpected return (ann.) : {pct(ret)}")
    print(f"Volatility     (ann.) : {pct(vol)}")
    print(f"Sharpe ratio (rf={pct(rf)}): {sharpe:.3f}\n")
    return ret, vol, sharpe


def save_weights(path, names, w):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        out = csv.writer(fh)
        out.writerow(["asset", "weight"])
        for n, x in zip(names, w):
            out.writerow([n, f"{x:.6f}"])
    print(f"Saved weights to {path}")


def percentish(x, what):
    """Accept 10 or 0.10 for 10%."""
    if abs(x) > 1.0:
        warn(f"{what}={x:g} interpreted as {x:g}% = {x / 100:g}")
        return x / 100.0
    return x


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_analyze(args):
    dates, names, P = load_prices(args.prices, args.ffill)
    ppy = detect_ppy(dates, args.ppy)
    rf = percentish(args.rf, "--rf")
    R, mu, cov = compute_stats(P, ppy)
    vol = np.sqrt(np.diag(cov))
    print_data_info(args.prices, dates, names, P, ppy)

    print("== Asset statistics (annualized) ==")
    rows = []
    for j, n in enumerate(names):
        sharpe = (mu[j] - rf) / vol[j] if vol[j] > 1e-12 else float("nan")
        rows.append((n, pct(mu[j]), pct(cagr(P[:, j], len(R), ppy)), pct(vol[j]),
                     f"{sharpe:.3f}", pct(max_drawdown(P[:, j]))))
    print(fmt_table(["Asset", "Return", "CAGR", "Volatility", "Sharpe", "MaxDD"], rows))

    corr = np.corrcoef(R, rowvar=False)
    print("\n== Correlation matrix ==")
    rows = [(n, *(f"{corr[i, j]:.2f}" for j in range(len(names)))) for i, n in enumerate(names)]
    print(fmt_table(["", *names], rows))
    print("\nLow/negative correlation pairs diversify best (MPT core idea).")


def cmd_optimize(args):
    dates, names, P = load_prices(args.prices, args.ffill)
    ppy = detect_ppy(dates, args.ppy)
    rf = percentish(args.rf, "--rf")
    _, mu, cov = compute_stats(P, ppy)
    bounds = build_bounds(len(names), args)
    print_data_info(args.prices, dates, names, P, ppy)

    if args.objective == "target-return":
        if args.target is None:
            die("--objective target-return needs --target (e.g. --target 0.10)")
        target = percentish(args.target, "--target")
        w = solve_target_return(mu, cov, target, bounds)
        if w is None:
            die(f"no feasible portfolio with expected return {pct(target)} "
                f"(reachable range depends on your assets and bounds)")
        title = f"Minimum volatility at target return {pct(target)}"
    elif args.objective == "min-vol":
        w = solve_min_vol(mu, cov, bounds)
        title = "Global minimum-variance portfolio"
    else:
        w = solve_max_sharpe(mu, cov, rf, bounds)
        title = "Maximum Sharpe ratio portfolio (tangency)"
    if w is None:
        die("optimization failed; try relaxing --min-weight/--max-weight")

    print_portfolio(title, w, names, mu, cov, rf)
    if args.save_weights:
        save_weights(args.save_weights, names, w)


def cmd_frontier(args):
    dates, names, P = load_prices(args.prices, args.ffill)
    ppy = detect_ppy(dates, args.ppy)
    rf = percentish(args.rf, "--rf")
    _, mu, cov = compute_stats(P, ppy)
    bounds = build_bounds(len(names), args)
    print_data_info(args.prices, dates, names, P, ppy)

    frontier, w_gmv = efficient_frontier(mu, cov, bounds, args.points)
    w_ms = solve_max_sharpe(mu, cov, rf, bounds)

    print(f"== Efficient frontier ({len(frontier)} points) ==")
    rows = []
    for t, w in frontier:
        ret, vol, sharpe = portfolio_perf(w, mu, cov, rf)
        rows.append((pct(ret), pct(vol), f"{sharpe:.3f}"))
    print(fmt_table(["Return", "Volatility", "Sharpe"], rows))
    print()
    print_portfolio("Global minimum-variance portfolio", w_gmv, names, mu, cov, rf)
    if w_ms is not None:
        print_portfolio("Maximum Sharpe ratio portfolio (tangency)", w_ms, names, mu, cov, rf)

    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8") as fh:
            out = csv.writer(fh)
            out.writerow(["return", "volatility", "sharpe", *names])
            for t, w in frontier:
                ret, vol, sharpe = portfolio_perf(w, mu, cov, rf)
                out.writerow([f"{ret:.6f}", f"{vol:.6f}", f"{sharpe:.4f}",
                              *(f"{x:.6f}" for x in w)])
        print(f"Saved frontier table to {args.out}")

    if args.plot:
        plot_frontier(args.plot, names, mu, cov, rf, frontier, w_gmv, w_ms, args.mc)


def plot_frontier(png, names, mu, cov, rf, frontier, w_gmv, w_ms, mc_n):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        warn("matplotlib not installed; skipping chart (pip install matplotlib)")
        return

    fig, ax = plt.subplots(figsize=(9, 6))

    if mc_n > 0:  # random long-only portfolios, colored by Sharpe
        rng = np.random.default_rng(20260520)
        W = rng.dirichlet(np.ones(len(mu)), size=mc_n)
        rets, vols = W @ mu, np.sqrt(np.einsum("ij,jk,ik->i", W, cov, W))
        sc = ax.scatter(vols * 100, rets * 100, c=(rets - rf) / vols, s=8, alpha=0.35,
                        cmap="viridis", linewidths=0)
        fig.colorbar(sc, ax=ax, label="Sharpe ratio")

    fr = [portfolio_perf(w, mu, cov, rf) for _, w in frontier]
    ax.plot([v * 100 for _, v, _ in fr], [r * 100 for r, _, _ in fr],
            color="crimson", lw=2.2, label="Efficient frontier")

    vols_a = np.sqrt(np.diag(cov))
    ax.scatter(vols_a * 100, mu * 100, marker="D", color="black", zorder=5, s=36,
               label="Individual assets")
    for n, x, y in zip(names, vols_a, mu):
        ax.annotate(f" {n}", (x * 100, y * 100), fontsize=8)

    r, v, _ = portfolio_perf(w_gmv, mu, cov, rf)
    ax.scatter([v * 100], [r * 100], marker="o", s=90, color="royalblue", zorder=6,
               edgecolors="white", label="Min variance (GMV)")
    if w_ms is not None:
        r, v, s = portfolio_perf(w_ms, mu, cov, rf)
        ax.scatter([v * 100], [r * 100], marker="*", s=280, color="orange", zorder=6,
                   edgecolors="black", label=f"Max Sharpe ({s:.2f})")
        # capital market line, without letting it stretch the axes
        xlim, ylim = (0, ax.get_xlim()[1]), ax.get_ylim()
        ax.plot([0, xlim[1]], [rf * 100, (rf + s * xlim[1] / 100) * 100], ls="--",
                lw=1.2, color="gray", label=f"Capital market line (rf={pct(rf)})")
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)

    ax.set_xlabel("Volatility, annualized (%)")
    ax.set_ylabel("Expected return, annualized (%)")
    ax.set_title("Efficient Frontier — Modern Portfolio Theory")
    ax.grid(alpha=0.3)
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    fig.savefig(png, dpi=150)
    print(f"Saved chart to {png}")


def load_holdings(path, names):
    """Read holdings CSV with columns asset + units|value. Returns units array."""
    try:
        with open(path, newline="", encoding="utf-8-sig") as fh:
            rows = [r for r in csv.reader(fh) if any(c.strip() for c in r)]
    except OSError as exc:
        die(f"cannot read holdings file: {exc}")
    if not rows:
        die(f"{path}: empty file")
    header = [h.strip().lower() for h in rows[0]]
    if "asset" not in header and "ticker" not in header:
        die(f"{path}: need a header row with columns: asset,units (or asset,value)")
    a_col = header.index("asset") if "asset" in header else header.index("ticker")
    if "units" in header:
        q_col, mode = header.index("units"), "units"
    elif "value" in header:
        q_col, mode = header.index("value"), "value"
    else:
        die(f"{path}: need a 'units' or 'value' column")

    lookup = {n.lower(): j for j, n in enumerate(names)}
    amounts = np.zeros(len(names))
    for i, row in enumerate(rows[1:], start=2):
        name = row[a_col].strip()
        j = lookup.get(name.lower())
        if j is None:
            die(f"{path} line {i}: asset {name!r} not found in the price file "
                f"(available: {', '.join(names)})")
        try:
            q = _parse_float(row[q_col])
        except ValueError:
            die(f"{path} line {i}: bad number {row[q_col]!r}")
        if q is None or q < 0:
            die(f"{path} line {i}: {mode} must be a number >= 0")
        amounts[j] += q
    return amounts, mode


def load_weight_file(path, names):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = [r for r in csv.reader(fh) if any(c.strip() for c in r)]
    header = [h.strip().lower() for h in rows[0]]
    if "asset" not in header or "weight" not in header:
        die(f"{path}: need header columns asset,weight")
    a_col, w_col = header.index("asset"), header.index("weight")
    lookup = {n.lower(): j for j, n in enumerate(names)}
    w = np.zeros(len(names))
    for i, row in enumerate(rows[1:], start=2):
        j = lookup.get(row[a_col].strip().lower())
        if j is None:
            die(f"{path} line {i}: asset {row[a_col]!r} not in the price file")
        w[j] = _parse_float(row[w_col]) or 0.0
    total = w.sum()
    if abs(total - 100.0) < 1.0:
        w /= 100.0
    elif abs(total - 1.0) > 0.01:
        warn(f"weights in {path} sum to {total:g}; renormalizing to 1")
        if total <= 0:
            die("weights must sum to a positive number")
        w /= total
    else:
        w /= w.sum()
    return w


def cmd_rebalance(args):
    dates, names, P = load_prices(args.prices, args.ffill)
    ppy = detect_ppy(dates, args.ppy)
    rf = percentish(args.rf, "--rf")
    _, mu, cov = compute_stats(P, ppy)
    last = P[-1]
    print_data_info(args.prices, dates, names, P, ppy)

    amounts, mode = load_holdings(args.holdings, names)
    cur_value = amounts * last if mode == "units" else amounts.copy()
    cur_units = amounts if mode == "units" else amounts / last
    total_now = float(cur_value.sum())
    total_target = total_now + args.cash
    if total_target <= 0:
        die("nothing to invest: current value + --cash must be positive")

    if args.weights:
        w_target = load_weight_file(args.weights, names)
        source = f"weights file {args.weights}"
    else:
        bounds = build_bounds(len(names), args)
        if args.objective == "min-vol":
            w_target = solve_min_vol(mu, cov, bounds)
        elif args.objective == "target-return":
            if args.target is None:
                die("--objective target-return needs --target")
            w_target = solve_target_return(mu, cov, percentish(args.target, "--target"), bounds)
        else:
            w_target = solve_max_sharpe(mu, cov, rf, bounds)
        source = f"optimizer objective '{args.objective}'"
        if w_target is None:
            die("optimization failed; try relaxing the bounds")

    tgt_value = w_target * total_target
    trade_value = tgt_value - cur_value
    trade_units = trade_value / last
    if args.lot > 0:
        trade_units = np.round(trade_units / args.lot) * args.lot
        trade_units = np.maximum(trade_units, -cur_units)  # cannot sell more than held
        trade_value = trade_units * last
    skip = np.abs(trade_value) < args.min_trade
    trade_units = np.where(skip, 0.0, trade_units)
    trade_value = np.where(skip, 0.0, trade_value)
    date_txt = f" @ {dates[-1]}" if dates else ""

    print(f"== Rebalance plan (target from {source}) ==")
    print(f"Current portfolio value : {total_now:,.2f}")
    if args.cash:
        print(f"Cash in/out             : {args.cash:+,.2f}")
    print(f"Value to allocate       : {total_target:,.2f}   (last prices{date_txt})\n")

    rows = []
    for j, n in enumerate(names):
        action = "-" if abs(trade_value[j]) < 0.005 else (
            "BUY" if trade_value[j] > 0 else "SELL")
        rows.append((n, f"{last[j]:,.2f}", f"{cur_units[j]:,.4f}", f"{cur_value[j]:,.2f}",
                     pct(cur_value[j] / total_now) if total_now > 0 else "-",
                     pct(w_target[j]), f"{tgt_value[j]:,.2f}", action,
                     f"{trade_value[j]:+,.2f}" if action != "-" else "0.00",
                     f"{trade_units[j]:+,.4f}" if action != "-" else "0"))
    print(fmt_table(["Asset", "Price", "Units", "Value", "Now%", "Target%",
                     "TargetValue", "Action", "Trade(Value)", "Trade(Units)"], rows))
    if skip.any():
        print(f"\n(trades below --min-trade {args.min_trade:g} are left as-is)")
    value_after = cur_value + trade_value
    residual = total_target - float(value_after.sum())
    if residual >= 0.005:
        print(f"Cash left unallocated after trades: {residual:,.2f}")
    elif residual <= -0.005:
        print(f"Rounded trades need {-residual:,.2f} extra cash; trim one BUY lot "
              f"or add that amount")

    print()
    if total_now > 0:
        print_portfolio("Portfolio BEFORE (current weights)", cur_value / total_now,
                        names, mu, cov, rf)
    if value_after.sum() > 0:
        print_portfolio("Portfolio AFTER (post-trade weights)", value_after / value_after.sum(),
                        names, mu, cov, rf)
    if not args.lot:
        print("Units are fractional; use --lot 100 to round to SET board lots.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("prices", help="CSV: date column (optional) then one price column per asset")
    common.add_argument("--rf", type=float, default=0.02,
                        help="annual risk-free rate, e.g. 0.02 or 2 (default 0.02)")
    common.add_argument("--ppy", type=float, default=None,
                        help="periods per year (default: auto-detect from dates; 252/52/12)")
    common.add_argument("--ffill", action="store_true",
                        help="carry the previous price forward over missing cells")

    opt = argparse.ArgumentParser(add_help=False)
    opt.add_argument("--objective", choices=["max-sharpe", "min-vol", "target-return"],
                     default="max-sharpe", help="what to optimize (default max-sharpe)")
    opt.add_argument("--target", type=float, default=None,
                     help="annual target return for --objective target-return (0.10 or 10)")
    opt.add_argument("--max-weight", type=float, default=None,
                     help="max weight per asset, e.g. 0.35")
    opt.add_argument("--min-weight", type=float, default=None,
                     help="min weight per asset (default 0, or -1 with --allow-short)")
    opt.add_argument("--allow-short", action="store_true",
                     help="allow short positions (weights may go negative)")

    p = argparse.ArgumentParser(
        prog="mpt.py",
        description="Modern Portfolio Theory portfolio manager (Markowitz mean-variance).")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("analyze", parents=[common],
                   help="per-asset stats + correlation matrix")

    s = sub.add_parser("optimize", parents=[common, opt],
                       help="find optimal portfolio weights")
    s.add_argument("--save-weights", metavar="FILE", help="write weights CSV (asset,weight)")

    s = sub.add_parser("frontier", parents=[common, opt],
                       help="efficient frontier table and chart")
    s.add_argument("--points", type=int, default=25, help="frontier points (default 25)")
    s.add_argument("--out", metavar="FILE", help="write frontier table CSV")
    s.add_argument("--plot", metavar="PNG", help="write efficient-frontier chart PNG")
    s.add_argument("--mc", type=int, default=3000,
                   help="random portfolios drawn on the chart (default 3000, 0=off)")

    s = sub.add_parser("rebalance", parents=[common, opt],
                       help="trade list from current holdings to target weights")
    s.add_argument("--holdings", required=True,
                   help="CSV of current holdings: asset,units (or asset,value)")
    s.add_argument("--weights", metavar="FILE",
                   help="target weights CSV (asset,weight); default: run the optimizer")
    s.add_argument("--cash", type=float, default=0.0,
                   help="extra cash to invest (negative = withdraw)")
    s.add_argument("--min-trade", type=float, default=0.0,
                   help="skip trades smaller than this value")
    s.add_argument("--lot", type=float, default=0.0,
                   help="round trade units to this lot size (SET board lot: 100)")
    return p


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    args = build_parser().parse_args(argv)
    handler = {"analyze": cmd_analyze, "optimize": cmd_optimize,
               "frontier": cmd_frontier, "rebalance": cmd_rebalance}[args.command]
    try:
        handler(args)
    except BrokenPipeError:  # e.g. `mpt.py ... | head`
        sys.exit(0)


if __name__ == "__main__":
    main()
