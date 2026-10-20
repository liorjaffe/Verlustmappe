#!/usr/bin/env python3
"""
auto_plot.py
============

A general-purpose CSV plotter for electrical measurements (Current /
Voltage / Power). Point it at any CSV and it will:

  1. Auto-detect which quantity each data column holds, based on the
     column header text (unit symbols and common keywords).
  2. Auto-detect a suitable x-axis (time / timestamp / sample index),
     parsing real timestamps as dates when possible.
  3. Plot every detected column at full resolution - no down-sampling,
     smoothing, or rounding of the underlying data - and format the
     y-axis with however many decimal places your data actually has,
     so you never see more (or less) precision than you recorded.
  4. If a file mixes multiple quantities (e.g. both Voltage and Current
     columns), it draws one stacked subplot per quantity, sharing the
     same x-axis, instead of squashing everything onto one scale.

--------------------------------------------------------------------------
USAGE  (VS Code integrated terminal, with your venv/conda env active)
--------------------------------------------------------------------------
    python auto_plot.py data.csv
    python auto_plot.py data.csv --columns "Ch1 Voltage (V),Ch2 Current (A)"
    python auto_plot.py data.csv --save plot.png
    python auto_plot.py data.csv --save plot.png --no-show
    python auto_plot.py                       # auto-picks the only *.csv in cwd

One-time setup:
    pip install pandas matplotlib numpy

Detection works off the column header text. Headers like "Voltage (V)",
"Current [A]", "Power (W)", "I", "U", "P", "Ch1 Amps" etc. are all
recognised. If a column can't be classified, it's skipped and reported -
rename the header (to include e.g. "V", "A", or "W") or pass --columns to
force which columns get plotted.
--------------------------------------------------------------------------
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


# ============================================================================
# 1. Detection rules
# ============================================================================
SIGNAL_RULES = {
    "current": {
        "patterns": [
            r"\bcurrent\b", r"\bamps?\b", r"\bamperes?\b",
            r"\(\s*[km]?a\s*\)", r"\[\s*[km]?a\s*\]",
            r"^i$", r"\bi\s*\(", r"_i$", r"\bi_",
        ],
        "unit": "A",
        "label": "Current",
    },
    "voltage": {
        "patterns": [
            r"\bvoltage\b", r"\bvolts?\b", r"\bvcc\b", r"\bvbus\b",
            r"\(\s*[km]?v\s*\)", r"\[\s*[km]?v\s*\]",
            r"^v$", r"^u$", r"\bv\s*\(", r"\bu\s*\(", r"_v$", r"\bv_",
        ],
        "unit": "V",
        "label": "Voltage",
    },
    "power": {
        "patterns": [
            r"\bpower\b", r"\bwatts?\b",
            r"\(\s*[km]?w\s*\)", r"\[\s*[km]?w\s*\]",
            r"^p$", r"\bp\s*\(", r"_p$", r"\bp_",
        ],
        "unit": "W",
        "label": "Power",
    },
}

TIME_PATTERNS = [
    r"\btime\b", r"\btimestamp\b", r"\bdate\b", r"\bt\s*\(",
    r"^t$", r"\bsample\b", r"\bindex\b", r"\belapsed\b",
]


def detect_signal(col_name: str) -> str | None:
    """Return 'current' / 'voltage' / 'power' / None for a header string."""
    name = col_name.lower().strip()
    for sig, rule in SIGNAL_RULES.items():
        for pat in rule["patterns"]:
            if re.search(pat, name):
                return sig
    return None


def looks_like_time(col_name: str) -> bool:
    name = col_name.lower().strip()
    return any(re.search(pat, name) for pat in TIME_PATTERNS)


# ============================================================================
# 2. Precision-aware axis formatting
# ============================================================================
def decimals_needed(values: np.ndarray, max_decimals: int = 6) -> int:
    """
    Work out how many decimal places are needed to represent the real
    resolution of the data, so axis labels never hide genuine variation
    by over-rounding, or show fake precision by under-rounding.
    """
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    if v.size < 2:
        return 2

    diffs = np.abs(np.diff(np.sort(np.unique(v))))
    diffs = diffs[diffs > 0]
    if diffs.size == 0:
        return 2

    smallest_step = diffs.min()
    if smallest_step <= 0:
        return 2

    decimals = int(np.ceil(-np.log10(smallest_step)))
    return int(np.clip(decimals, 0, max_decimals))


def make_formatter(values: np.ndarray) -> mticker.FuncFormatter:
    d = decimals_needed(values)
    return mticker.FuncFormatter(lambda x, _pos: f"{x:,.{d}f}")


# ============================================================================
# 3. Loading
# ============================================================================
def load_csv(path: Path) -> pd.DataFrame:
    # sep=None + engine="python" lets pandas sniff comma / semicolon / tab.
    df = pd.read_csv(path, sep=None, engine="python")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def pick_x_column(df: pd.DataFrame) -> str:
    for col in df.columns:
        if looks_like_time(col):
            return col
    return df.columns[0]


def coerce_x(series: pd.Series) -> tuple[np.ndarray, bool]:
    """
    Return (values, is_datetime). Numeric columns (elapsed seconds, sample
    counts, etc.) are checked first, since plain numbers like 0.0, 0.001 ...
    would otherwise get silently misread as 1970-01-01 epoch timestamps.
    Real date/time strings only reach the datetime branch because they
    fail the numeric parse.
    """
    as_num = pd.to_numeric(series, errors="coerce")
    if as_num.notna().mean() > 0.9:
        return as_num.to_numpy(), False
    as_dt = pd.to_datetime(series, errors="coerce")
    if as_dt.notna().mean() > 0.9:
        return as_dt.to_numpy(), True
    return np.arange(len(series)), False


def find_default_csv() -> Path:
    candidates = sorted(Path.cwd().glob("*.csv"))
    if not candidates:
        sys.exit("No CSV path given and no *.csv file found in the current folder.")
    if len(candidates) > 1:
        names = ", ".join(c.name for c in candidates)
        sys.exit(
            f"No CSV path given and multiple CSVs found ({names}). "
            f"Re-run with: python auto_plot.py <file.csv>"
        )
    return candidates[0]


# ============================================================================
# 4. Main
# ============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Auto-detect and plot Current / Voltage / Power CSV data."
    )
    parser.add_argument(
        "csv", nargs="?",
        help="Path to the CSV file (optional if exactly one *.csv is in the current folder).",
    )
    parser.add_argument(
        "--columns",
        help="Comma-separated list of column names to plot (default: all detectable columns).",
    )
    parser.add_argument("--save", help="Save the figure to this path (e.g. plot.png).")
    parser.add_argument(
        "--no-show", action="store_true",
        help="Don't open an interactive window (useful together with --save).",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv) if args.csv else find_default_csv()
    if not csv_path.exists():
        sys.exit(f"File not found: {csv_path}")

    df = load_csv(csv_path)
    if df.shape[1] < 2:
        sys.exit("CSV needs at least two columns (an x-axis and one data column).")

    x_col = pick_x_column(df)
    x_values, x_is_datetime = coerce_x(df[x_col])

    if args.columns:
        wanted = {c.strip() for c in args.columns.split(",")}
        data_cols = [c for c in df.columns if c in wanted]
        missing = wanted - set(data_cols)
        if missing:
            sys.exit(f"Column(s) not found in CSV: {', '.join(missing)}")
    else:
        data_cols = [c for c in df.columns if c != x_col]

    # Bucket columns by detected signal type; skip non-numeric / unrecognised ones.
    buckets: dict[str, list[str]] = {"current": [], "voltage": [], "power": []}
    unrecognised = []
    for col in data_cols:
        numeric = pd.to_numeric(df[col], errors="coerce")
        if numeric.notna().mean() < 0.5:
            continue  # not really numeric data - skip silently
        sig = detect_signal(col)
        if sig:
            buckets[sig].append(col)
        else:
            unrecognised.append(col)

    active_types = [t for t in ("voltage", "current", "power") if buckets[t]]

    if not active_types:
        if unrecognised:
            sys.exit(
                "Couldn't tell Current / Voltage / Power apart from these column "
                f"headers: {unrecognised}. Rename the columns to include e.g. "
                "'Voltage (V)', 'Current (A)', or 'Power (W)', or pass --columns explicitly."
            )
        sys.exit("No numeric data columns found to plot.")

    if unrecognised:
        print(f"Note: skipping column(s) I couldn't classify as Current/Voltage/Power: {unrecognised}")

    # --------------------------------------------------------------------
    # Plot: one subplot per detected quantity, sharing the x-axis.
    # --------------------------------------------------------------------
    fig, axes = plt.subplots(
        nrows=len(active_types), ncols=1,
        sharex=True, squeeze=False,
        figsize=(10, 3.2 * len(active_types)),
    )
    axes = axes[:, 0]

    for ax, sig in zip(axes, active_types):
        rule = SIGNAL_RULES[sig]
        cols = buckets[sig]
        all_vals = []

        for col in cols:
            y = pd.to_numeric(df[col], errors="coerce").to_numpy()
            all_vals.append(y)
            n_pts = np.sum(~np.isnan(y))
            marker = "o" if n_pts <= 200 else None
            ax.plot(x_values, y, marker=marker, markersize=3, linewidth=1.2, label=col)

        ax.set_ylabel(cols[0] if len(cols) == 1 else f'{rule["label"]} ({rule["unit"]})')
        ax.yaxis.set_major_formatter(make_formatter(np.concatenate(all_vals)))
        ax.grid(True, alpha=0.3)
        if len(cols) > 1:
            ax.legend(fontsize=8)

    axes[-1].set_xlabel(x_col)
    if x_is_datetime:
        fig.autofmt_xdate()

    fig.suptitle(csv_path.name, fontsize=11)
    fig.tight_layout()

    if args.save:
        fig.savefig(args.save, dpi=200, bbox_inches="tight")
        print(f"Saved plot to {args.save}")

    if not args.no_show:
        plt.show()


if __name__ == "__main__":
    main()
