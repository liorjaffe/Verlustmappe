"""Publication-style plots, all testable on synthetic data. Outputs PNG + PDF."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def plot_loss_map(accounts, fname="loss_map"):
    """accounts: ordered list of dicts. Accepts the loss_map() bar format
    ({stage, kWh, status}) OR the legacy device-account format ({unit,
    loss_kwh}). Status labels are drawn on every bar (Rule 3)."""
    labels, values, statuses = [], [], []
    total = 0.0
    for a in accounts:
        if "stage" in a and "kWh" in a:
            labels.append(a["stage"]); values.append(a["kWh"]); statuses.append(a.get("status", ""))
        elif a.get("loss_kwh") is not None:
            labels.append(a.get("unit", "?")); values.append(a["loss_kwh"]); statuses.append("")
        elif "energy_in_kwh" in a:
            total = a["energy_in_kwh"]
    if not labels:
        raise ValueError("plot_loss_map: no bars to draw (empty or wrong input format)")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(labels, values, color="#c0392b")
    for x, (v, st) in enumerate(zip(values, statuses)):
        if st: ax.text(x, v, st, ha="center", va="bottom", fontsize=7, rotation=45)
    ax.set_ylabel("Energy loss [kWh]")
    ax.set_title(f"Loss map (input {total:.1f} kWh)")
    fig.tight_layout(); fig.savefig(f"{fname}.png", dpi=200); fig.savefig(f"{fname}.pdf")
    plt.close(fig)
    return f"{fname}.png"

def plot_rte_by_mode(rte_by_mode, fname="rte_by_mode"):
    """rte_by_mode: dict mode -> rte fraction."""
    modes = list(rte_by_mode); vals = [100*rte_by_mode[m] for m in modes]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(modes, vals, color="#2471a3")
    ax.set_ylabel("Round-trip efficiency [%]")
    ax.set_title("RTE by operating mode")
    for x, v in zip(modes, vals):
        ax.text(x, v, f"{v:.1f}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout(); fig.savefig(f"{fname}.png", dpi=200); fig.savefig(f"{fname}.pdf")
    plt.close(fig)
    return f"{fname}.png"

def plot_routes(routes, fname="gas_routes"):
    """routes: list of dicts route -> kg. Bar comparison + spread annotation."""
    names = [r["route"] for r in routes]
    g = [r["kg"]*1000 for r in routes]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(names, g, color="#1e8449")
    ax.set_ylabel("H2 mass [g]")
    spread = (max(g)-min(g))/np.mean(g)*100 if np.mean(g) else 0
    ax.set_title(f"H2 route comparison (spread {spread:.1f}%)")
    fig.tight_layout(); fig.savefig(f"{fname}.png", dpi=200); fig.savefig(f"{fname}.pdf")
    plt.close(fig)
    return f"{fname}.png"

def plot_uncertainty_band(band, fname="rte_uncertainty"):
    mean = band.get("rte_mean", band.get("mean"))
    lo = band.get("rte_lo", band.get("lo")); hi = band.get("rte_hi", band.get("hi"))
    if mean is None or lo is None or hi is None:
        raise ValueError("plot_uncertainty_band: need rte_mean/rte_lo/rte_hi (or mean/lo/hi)")
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.errorbar([0], [100*mean], yerr=[[100*(mean-lo)], [100*(hi-mean)]], fmt="o", capsize=8, color="#2471a3")
    ax.set_xticks([]); ax.set_ylabel("RTE [%]")
    ax.set_title(f"Monte-Carlo band, n={band.get('n', '?')}")
    fig.tight_layout(); fig.savefig(f"{fname}.png", dpi=200); fig.savefig(f"{fname}.pdf")
    plt.close(fig)
    return f"{fname}.png"
