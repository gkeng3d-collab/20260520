#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate deterministic sample data for mpt.py.

Writes sample_prices.csv (3 years of daily prices for 5 synthetic assets)
and sample_holdings.csv (an example current portfolio). Re-running always
produces identical files (fixed RNG seed).
"""

import csv
from datetime import date, timedelta

import numpy as np

SEED = 20260520
START = date(2023, 8, 1)
DAYS = 757  # price rows -> 756 daily returns (~3 trading years)

ASSETS = ["THAI_EQ", "GLOBAL_EQ", "TECH", "BOND", "GOLD"]
START_PRICE = [10.0, 100.0, 250.0, 12.0, 30.0]
MU_ANNUAL = [0.06, 0.09, 0.14, 0.03, 0.07]     # arithmetic, per year
VOL_ANNUAL = [0.16, 0.18, 0.28, 0.05, 0.15]
CORR = np.array([
    [1.00, 0.55, 0.45, 0.10, 0.15],
    [0.55, 1.00, 0.80, 0.05, 0.10],
    [0.45, 0.80, 1.00, 0.00, 0.05],
    [0.10, 0.05, 0.00, 1.00, 0.20],
    [0.15, 0.10, 0.05, 0.20, 1.00],
])

HOLDINGS = [("THAI_EQ", 12000), ("GLOBAL_EQ", 1500), ("BOND", 5000), ("GOLD", 800)]


def business_days(start, count):
    out, d = [], start
    while len(out) < count:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def main():
    ppy = 252.0
    mu_d = np.array(MU_ANNUAL) / ppy
    vol_d = np.array(VOL_ANNUAL) / np.sqrt(ppy)
    cov_d = CORR * np.outer(vol_d, vol_d)
    np.linalg.cholesky(cov_d)  # fail fast if CORR is not positive definite

    rng = np.random.default_rng(SEED)
    returns = rng.multivariate_normal(mu_d, cov_d, size=DAYS - 1)
    prices = START_PRICE * np.cumprod(np.vstack([np.ones(len(ASSETS)), 1 + returns]), axis=0)

    dates = business_days(START, DAYS)
    with open("sample_prices.csv", "w", newline="", encoding="utf-8") as fh:
        out = csv.writer(fh)
        out.writerow(["date", *ASSETS])
        for d, row in zip(dates, prices):
            out.writerow([d.isoformat(), *(f"{p:.4f}" for p in row)])

    with open("sample_holdings.csv", "w", newline="", encoding="utf-8") as fh:
        out = csv.writer(fh)
        out.writerow(["asset", "units"])
        out.writerows(HOLDINGS)

    print(f"sample_prices.csv   : {len(ASSETS)} assets x {DAYS} rows "
          f"({dates[0]} .. {dates[-1]})")
    print("sample_holdings.csv : example portfolio (asset,units)")


if __name__ == "__main__":
    main()
