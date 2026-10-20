#!/usr/bin/env python3
"""
auto_plot_interactive.py
=========================

Same auto-detection as auto_plot.py (Current / Voltage / Power, from your
CSV's column headers) but renders an interactive HTML plot with Plotly
instead of a static matplotlib window.

Why this version: Plotly's zoom/pan/hover works reliably everywhere
(no backend quirks), and hovering over any point shows the exact
time + value at full precision - handy for zooming into a specific
cycle/event and reading off exact numbers.

--------------------------------------------------------------------------
USAGE
--------------------------------------------------------------------------
    python3 auto_plot_interactive.py data.csv
    python3 auto_plot_interactive.py data.csv --columns "Current (A)"
    python3 auto_plot_interactive.py data.csv --save myplot.html --no-open

One-time setup:
    pip install pandas plotly numpy
    (or, if you hit the "externally managed environment" error:
     pip install pandas plotly numpy --break-system-packages,
     or better: use the same venv you already set up for auto_plot.py)

In the browser tab that opens:
    - Click-drag  -> zoom into a box
    - Double-click -> reset zoom
    - Scroll / toolbar icons -> pan, zoom in/out, autoscale
    - Hover        -> exact x/y value at that point
--------------------------------------------------------------------------
"""
from __future__ import annotations

import argparse
import re
import sys
import webbrowser
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ============================================================================
# Detection rules (identical logic to auto_plot.py)
# ============================================================================
SIGNAL_RULES = {
    "current": {
        "patterns": [
            r"\bcurrent\b", r"\bamps?\b", r"\bamperes?\b",
            r"\(\s*[km]?a\s*\)", r"\[\s*[km]?a\s*\]",
            r"^i$", r"\bi\s*\(", r"_i$", r"\bi_",
        ],
        "unit": "A", "label": "Current",
    },
    "voltage": {
        "patterns": [
            r"\bvoltage\b", r"\bvolts?\b", r"\bvcc\b", r"\bvbus\b",
            r"\(\s*[km]?v\s*\)", r"\[\s*[km]?v\s*\]",
            r"^v$", r"^u$", r"\bv\s*\(", r"\bu\s*\(", r"_v$", r"\bv_",
        ],
        "unit": "V", "label": "Voltage",
    },
    "power": {
        "patterns": [
            r"\bpower\b", r"\bwatts?\b",
            r"\(\s*[km]?w\s*\)", r"\[\s*[km]?w\s*\]",
            r"^p$", r"\bp\s*\(", r"_p$", r"\bp_",
        ],
        "unit": "W", "label": "Power",
    },
}

TIME_PATTERNS = [
    r"\btime\b", r"\btimestamp\b", r"\bdate\b", r"\bt\s*\(",
    r"^t$", r"\bsample\b", r"\bindex\b", r"\belapsed\b",
]


def detect_signal(col_name: str) -> str | None:
    name = col_name.lower().strip()
    for sig, rule in SIGNAL_RULES.items():
        for pat in rule["patterns"]:
            if re.search(pat, name):
                return sig
    return None


def looks_like_time(col_name: str) -> bool:
    name = col_name.lower().strip()
    return any(re.search(pat, name) for pat in TIME_PATTERNS)


def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=None, engine="python")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def pick_x_column(df: pd.DataFrame) -> str:
    for col in df.columns:
        if looks_like_time(col):
            return col
    return df.columns[0]


def coerce_x(series: pd.Series) -> tuple[np.ndarray, bool]:
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
        sys.exit(f"No CSV path given and multiple CSVs found ({names}). "
                  f"Re-run with: python3 auto_plot_interactive.py <file.csv>")
    return candidates[0]


# ============================================================================
# Main
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description="Interactive (Plotly) Current/Voltage/Power CSV plot.")
    parser.add_argument("csv", nargs="?", help="Path to the CSV (optional if exactly one *.csv is in the current folder).")
    parser.add_argument("--columns", help="Comma-separated list of column names to plot.")
    parser.add_argument("--save", help="Output HTML path (default: <csvname>_interactive.html).")
    parser.add_argument("--no-open", action="store_true", help="Don't auto-open the HTML file in a browser.")
    args = parser.parse_args()

    csv_path = Path(args.csv) if args.csv else find_default_csv()
    if not csv_path.exists():
        sys.exit(f"File not found: {csv_path}")

    df = load_csv(csv_path)
    if df.shape[1] < 2:
        sys.exit("CSV needs at least two columns (an x-axis and one data column).")

    x_col = pick_x_column(df)
    x_values, _x_is_datetime = coerce_x(df[x_col])

    if args.columns:
        wanted = {c.strip() for c in args.columns.split(",")}
        data_cols = [c for c in df.columns if c in wanted]
        missing = wanted - set(data_cols)
        if missing:
            sys.exit(f"Column(s) not found in CSV: {', '.join(missing)}")
    else:
        data_cols = [c for c in df.columns if c != x_col]

    buckets: dict[str, list[str]] = {"current": [], "voltage": [], "power": []}
    unrecognised = []
    for col in data_cols:
        numeric = pd.to_numeric(df[col], errors="coerce")
        if numeric.notna().mean() < 0.5:
            continue
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

    fig = make_subplots(
        rows=len(active_types), cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=[f'{SIGNAL_RULES[t]["label"]}' for t in active_types],
    )

    for row, sig in enumerate(active_types, start=1):
        rule = SIGNAL_RULES[sig]
        cols = buckets[sig]
        for col in cols:
            y = pd.to_numeric(df[col], errors="coerce").to_numpy()
            fig.add_trace(
                go.Scattergl(
                    x=x_values, y=y, mode="lines",
                    name=col,
                    hovertemplate=f"{x_col}: %{{x}}<br>{col}: %{{y:.6g}}<extra></extra>",
                ),
                row=row, col=1,
            )
        # fixedrange=True: dragging a zoom box only zooms the time (x) axis,
        # so you never accidentally lose the full y-range while zooming in
        # on a time window. Double-click still resets fully.
        fig.update_yaxes(title_text=f'{rule["label"]} ({rule["unit"]})', fixedrange=True, row=row, col=1)

    fig.update_xaxes(title_text=x_col, rangeslider=dict(visible=True), row=len(active_types), col=1)
    fig.update_layout(
        title=csv_path.name,
        height=350 * len(active_types) + 60,
        hovermode="x unified",
        template="plotly_white",
        dragmode="pan",  # drag to slide the view; use the range slider or scroll to zoom
    )

    out_path = Path(args.save) if args.save else csv_path.with_name(csv_path.stem + "_interactive.html")
    fig.write_html(out_path, include_plotlyjs="cdn", config={"scrollZoom": True})
    print(f"Saved interactive plot to {out_path}")

    if not args.no_open:
        webbrowser.open(f"file://{out_path.resolve()}")


if __name__ == "__main__":
    main()
