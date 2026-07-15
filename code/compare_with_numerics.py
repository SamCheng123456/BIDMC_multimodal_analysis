from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


WINDOW_SECONDS = 30

plt.rcParams["font.family"] = ["Times New Roman", "SimSun", "DejaVu Serif"]
plt.rcParams["font.size"] = 10.5
plt.rcParams["axes.unicode_minus"] = False


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_numerics(raw_dir: Path, record_id: str) -> pd.DataFrame:
    path = raw_dir / f"bidmc_{record_id}_Numerics.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    return df


def window_monitor_values(numerics: pd.DataFrame, window_start: float, window_end: float) -> dict[str, float]:
    t = numerics["Time [s]"].to_numpy(dtype=float)
    mask = (t >= window_start) & (t < window_end)
    if not np.any(mask):
        return {"monitor_hr_bpm": np.nan, "monitor_pulse_bpm": np.nan, "monitor_resp_bpm": np.nan}
    out: dict[str, float] = {}
    for src, dst in [("HR", "monitor_hr_bpm"), ("PULSE", "monitor_pulse_bpm"), ("RESP", "monitor_resp_bpm")]:
        values = pd.to_numeric(numerics.loc[mask, src], errors="coerce")
        values = values.replace(0, np.nan)
        out[dst] = float(values.mean()) if values.notna().any() else np.nan
    return out


def build_comparison(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    features = pd.read_csv(root / "results" / "full_dataset_window_features.csv", dtype={"record_id": str})
    rows = []
    for record_id, group in features.groupby("record_id"):
        numerics = read_numerics(root / "data" / "raw", record_id)
        for row in group.itertuples(index=False):
            monitor = window_monitor_values(numerics, float(row.window_start_s), float(row.window_end_s))
            rows.append(
                {
                    "record_id": record_id,
                    "window_start_s": float(row.window_start_s),
                    "window_end_s": float(row.window_end_s),
                    "ecg_hr_bpm": float(row.ecg_hr_bpm),
                    "ppg_pr_bpm": float(row.ppg_pr_bpm),
                    "resp_rr_bpm": float(row.resp_rr_bpm),
                    **monitor,
                }
            )

    comp = pd.DataFrame(rows)
    comp["ecg_vs_monitor_hr_abs_error"] = (comp["ecg_hr_bpm"] - comp["monitor_hr_bpm"]).abs()
    comp["ppg_vs_monitor_pulse_abs_error"] = (comp["ppg_pr_bpm"] - comp["monitor_pulse_bpm"]).abs()
    comp["resp_vs_monitor_resp_abs_error"] = (comp["resp_rr_bpm"] - comp["monitor_resp_bpm"]).abs()

    summary = (
        comp.groupby("record_id")
        .agg(
            windows=("window_start_s", "count"),
            monitor_hr_mean=("monitor_hr_bpm", "mean"),
            monitor_pulse_mean=("monitor_pulse_bpm", "mean"),
            monitor_resp_mean=("monitor_resp_bpm", "mean"),
            ecg_hr_mean=("ecg_hr_bpm", "mean"),
            ppg_pr_mean=("ppg_pr_bpm", "mean"),
            resp_rr_mean=("resp_rr_bpm", "mean"),
            ecg_monitor_mae=("ecg_vs_monitor_hr_abs_error", "mean"),
            ppg_monitor_mae=("ppg_vs_monitor_pulse_abs_error", "mean"),
            resp_monitor_mae=("resp_vs_monitor_resp_abs_error", "mean"),
        )
        .reset_index()
    )
    summary["signal_quality_flag"] = np.where(
        (summary["ecg_monitor_mae"] > 10)
        | (summary["ppg_monitor_mae"] > 10)
        | (summary["resp_monitor_mae"] > 6),
        "review",
        "ok",
    )
    return comp, summary


def plot_comparison(comp: pd.DataFrame, summary: pd.DataFrame, root: Path) -> None:
    fig_dir = root / "figures" / "full_dataset"
    fig_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 9, "axes.grid": True})

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    metrics = [
        ("ecg_vs_monitor_hr_abs_error", "ECG HR vs monitor HR", "bpm", "#2563EB"),
        ("ppg_vs_monitor_pulse_abs_error", "PPG PR vs monitor pulse", "bpm", "#0EA5E9"),
        ("resp_vs_monitor_resp_abs_error", "RESP RR vs monitor RESP", "breaths/min", "#14B8A6"),
    ]
    for ax, (col, title, unit, color) in zip(axes, metrics):
        values = comp[col].dropna().to_numpy(dtype=float)
        ax.hist(values, bins=30, color=color, alpha=0.82, edgecolor="white")
        ax.axvline(np.nanmedian(values), color="#111827", linewidth=1.2, label=f"Median {np.nanmedian(values):.2f}")
        ax.set_title(title)
        ax.set_xlabel(f"Absolute error ({unit})")
        ax.set_ylabel("Window count")
        ax.legend(fontsize=8)
    fig.suptitle("Signal-Derived Estimates vs Monitor Numerics")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig23_signal_vs_monitor_error_distribution.png", dpi=300)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    pairs = [
        ("monitor_hr_bpm", "ecg_hr_bpm", "Monitor HR", "ECG HR", "#2563EB"),
        ("monitor_pulse_bpm", "ppg_pr_bpm", "Monitor pulse", "PPG PR", "#0EA5E9"),
        ("monitor_resp_bpm", "resp_rr_bpm", "Monitor RESP", "RESP RR", "#14B8A6"),
    ]
    for ax, (xcol, ycol, xlabel, ylabel, color) in zip(axes, pairs):
        x = comp[xcol].to_numpy(dtype=float)
        y = comp[ycol].to_numpy(dtype=float)
        mask = np.isfinite(x) & np.isfinite(y)
        ax.scatter(x[mask], y[mask], s=14, alpha=0.35, color=color, linewidths=0)
        lo = min(np.nanmin(x[mask]), np.nanmin(y[mask]))
        hi = max(np.nanmax(x[mask]), np.nanmax(y[mask]))
        ax.plot([lo, hi], [lo, hi], color="#111827", linewidth=1.0, linestyle="--")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(f"{ylabel} agreement")
    fig.suptitle("Signal and Monitor Agreement Across Full Dataset")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig24_signal_monitor_agreement_scatter.png", dpi=300)
    plt.close(fig)

    ranked = summary.sort_values("ecg_monitor_mae", ascending=False)
    fig, ax = plt.subplots(figsize=(10, max(7.5, len(ranked) * 0.14)))
    y = np.arange(len(ranked))
    colors = np.where(ranked["signal_quality_flag"] == "review", "#DC2626", "#93C5FD")
    ax.barh(y, ranked["ecg_monitor_mae"], color=colors)
    ax.set_yticks(y, ranked["record_id"].astype(str))
    ax.invert_yaxis()
    ax.set_title("Record-Level ECG-vs-Monitor Error Ranking")
    ax.set_xlabel("Mean absolute error (bpm)")
    ax.set_ylabel("BIDMC record")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig25_record_quality_flags.png", dpi=300)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare signal-derived BIDMC estimates with monitor numerics.")
    return parser.parse_args()


def main() -> None:
    parse_args()
    root = project_root()
    comp, summary = build_comparison(root)
    comp.to_csv(root / "results" / "full_dataset_monitor_comparison.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(root / "results" / "full_dataset_monitor_comparison_summary.csv", index=False, encoding="utf-8-sig")
    plot_comparison(comp, summary, root)
    print("Monitor comparison complete.")
    print(root / "results" / "full_dataset_monitor_comparison_summary.csv")


if __name__ == "__main__":
    main()
