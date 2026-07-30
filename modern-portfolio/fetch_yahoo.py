#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch adjusted-close price history from Yahoo Finance into a CSV for mpt.py.

Needs only the Python standard library. Run it on a machine with normal
internet access (some sandboxes block Yahoo). Examples:

    python fetch_yahoo.py SPALI.BK DCC.BK GOLD --out prices.csv
    python fetch_yahoo.py --holdings my-port/holdings.csv --suffix .BK \
        --out my-port/prices.csv

Thai stocks/REITs on Yahoo use the .BK suffix (SPALI.BK, LHHOTEL.BK, ...).
With --suffix .BK the suffix is appended for fetching but stripped from the
CSV column names, so they match the asset names in your holdings file.
Prices are dividend/split-adjusted (adjclose) when Yahoo provides it.
"""

import argparse
import csv
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone

API = ("https://query1.finance.yahoo.com/v8/finance/chart/"
       "{sym}?range={rng}&interval={itv}&events=div%2Csplit")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def fetch(sym, rng, itv, retries=3):
    url = API.format(sym=sym, rng=rng, itv=itv)
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.load(resp)
            result = data["chart"]["result"][0]
            stamps = result["timestamp"]
            ind = result["indicators"]
            closes = (ind.get("adjclose", [{}])[0].get("adjclose")
                      or ind["quote"][0]["close"])
            series = {}
            for t, c in zip(stamps, closes):
                if c is not None:
                    series[datetime.fromtimestamp(t, tz=timezone.utc).date()] = float(c)
            if len(series) < 3:
                raise ValueError("Yahoo returned almost no data")
            return series
        except Exception as exc:  # noqa: BLE001 - retry then report
            last_err = exc
            time.sleep(2 * (attempt + 1))
    sys.exit(f"error fetching {sym}: {last_err} "
             f"(check the symbol on finance.yahoo.com, e.g. SPALI.BK)")


def main():
    ap = argparse.ArgumentParser(
        description="Fetch Yahoo Finance history into a CSV for mpt.py")
    ap.add_argument("tickers", nargs="*", help="Yahoo symbols, e.g. SPALI.BK")
    ap.add_argument("--holdings", help="also read asset names from this holdings CSV")
    ap.add_argument("--suffix", default="",
                    help="appended to names for fetching, stripped from CSV columns (.BK)")
    ap.add_argument("--range", dest="rng", default="3y",
                    help="1y | 2y | 3y | 5y | max (default 3y)")
    ap.add_argument("--interval", default="1d", help="1d | 1wk | 1mo (default 1d)")
    ap.add_argument("--out", default="prices.csv", help="output CSV (default prices.csv)")
    args = ap.parse_args()

    symbols = list(args.tickers)
    if args.holdings:
        with open(args.holdings, newline="", encoding="utf-8-sig") as fh:
            rows = [r for r in csv.reader(fh) if any(c.strip() for c in r)]
        header = [h.strip().lower() for h in rows[0]]
        if "asset" not in header:
            sys.exit(f"{args.holdings}: no 'asset' column in header")
        col = header.index("asset")
        symbols += [r[col].strip() + args.suffix for r in rows[1:] if r[col].strip()]
    if not symbols:
        ap.error("no tickers given (positional arguments or --holdings)")

    series, names = {}, []
    for sym in symbols:
        name = sym[:-len(args.suffix)] if args.suffix and sym.endswith(args.suffix) else sym
        if name in series:
            continue
        print(f"fetching {sym} ...", flush=True)
        series[name] = fetch(sym, args.rng, args.interval)
        names.append(name)
        time.sleep(0.8)  # be polite to Yahoo

    # align on the union of dates from the latest common start; forward-fill gaps
    start = max(min(s) for s in series.values())
    dates = sorted(d for d in set().union(*series.values()) if d >= start)
    last = {n: series[n][max(d for d in series[n] if d <= start)] for n in names}
    dropped = {n: sum(1 for d in series[n] if d < start) for n in names}

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        out = csv.writer(fh)
        out.writerow(["date", *names])
        for d in dates:
            row = [d.isoformat()]
            for n in names:
                last[n] = series[n].get(d, last[n])
                row.append(f"{last[n]:.6f}")
            out.writerow(row)

    print(f"\nwrote {args.out}: {len(names)} assets x {len(dates)} rows "
          f"({dates[0]} .. {dates[-1]})")
    trimmed = {n: k for n, k in dropped.items() if k}
    if trimmed:
        limiter = min(names, key=lambda n: (min(series[n]) != start, n))
        print(f"note: history starts at {start} because {limiter} has no data before "
              f"that; {len(trimmed)} asset(s) had earlier rows trimmed")
    print(f"next: python mpt.py analyze {args.out}")


if __name__ == "__main__":
    main()
