from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import main


plt.rcParams["font.family"] = ["Times New Roman", "SimSun", "DejaVu Serif"]
plt.rcParams["font.size"] = 10.5
plt.rcParams["axes.unicode_minus"] = False


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Advanced multimodal fusion analysis for BIDMC records.")
    parser.add_argument("--records", nargs="+", default=["01", "02", "03"], help="Record numbers to analyze.")
    return parser.parse_args()


def match_pulse_arrival_times(ecg_peaks: np.ndarray, ppg_peaks: np.ndarray, fs: float) -> pd.DataFrame:
    rows = []
    min_delay = int(0.08 * fs)
    max_delay = int(0.60 * fs)
    ppg_pos = 0

    for r_peak in ecg_peaks:
        while ppg_pos < len(ppg_peaks) and ppg_peaks[ppg_pos] < r_peak + min_delay:
            ppg_pos += 1
        if ppg_pos >= len(ppg_peaks):
            break
        p_peak = ppg_peaks[ppg_pos]
        delay = p_peak - r_peak
        if min_delay <= delay <= max_delay:
            rows.append(
                {
                    "r_peak_sample": int(r_peak),
                    "ppg_peak_sample": int(p_peak),
                    "r_peak_time_s": float(r_peak / fs),
                    "ppg_peak_time_s": float(p_peak / fs),
                    "pulse_arrival_time_ms": float(delay / fs * 1000),
                }
            )
    return pd.DataFrame(rows)


def robust_zscore(series: pd.Series) -> pd.Series:
    med = series.median()
    mad = (series - med).abs().median()
    if mad == 0 or np.isnan(mad):
        return series - med
    return 0.6745 * (series - med) / mad


def clean_pat_table(pat: pd.DataFrame) -> pd.DataFrame:
    if pat.empty:
        return pat
    z = robust_zscore(pat["pulse_arrival_time_ms"])
    return pat[z.abs() <= 3.5].copy()


def analyze_record(record_id: str, root: Path) -> tuple[pd.DataFrame, dict[str, float]]:
    record = main.load_bidmc_csv(root / "data" / "raw", record_id)
    clean = main.preprocess(record)
    ecg_peaks = main.peak_indices(clean["ecg"], record.fs, "ecg")
    ppg_peaks = main.peak_indices(clean["ppg"], record.fs, "ppg")
    pat = match_pulse_arrival_times(ecg_peaks, ppg_peaks, record.fs)
    pat = clean_pat_table(pat)
    pat.insert(0, "record_id", record_id)

    features = pd.read_csv(root / "results" / f"{record_id}_features.csv", dtype={"record_id": str})
    features["record_id"] = record_id
    hr_pr_corr = features["ecg_hr_bpm"].corr(features["ppg_pr_bpm"])
    hr_resp_corr = features["ecg_hr_bpm"].corr(features["resp_rr_bpm"])
    pr_resp_corr = features["ppg_pr_bpm"].corr(features["resp_rr_bpm"])

    summary = {
        "record_id": record_id,
        "pat_count": int(len(pat)),
        "pat_mean_ms": float(pat["pulse_arrival_time_ms"].mean()) if not pat.empty else np.nan,
        "pat_std_ms": float(pat["pulse_arrival_time_ms"].std(ddof=1)) if len(pat) > 1 else np.nan,
        "pat_median_ms": float(pat["pulse_arrival_time_ms"].median()) if not pat.empty else np.nan,
        "ecg_ppg_rate_corr": float(hr_pr_corr),
        "ecg_resp_rate_corr": float(hr_resp_corr),
        "ppg_resp_rate_corr": float(pr_resp_corr),
    }
    return pat, summary


def plot_pat_distribution(pat_all: pd.DataFrame, fig_dir: Path) -> None:
    records = sorted(pat_all["record_id"].unique())
    data = [pat_all.loc[pat_all["record_id"] == r, "pulse_arrival_time_ms"].dropna().to_numpy() for r in records]

    fig, ax = plt.subplots(figsize=(max(8.5, len(records) * 0.28), 5.5))
    bp = ax.boxplot(data, labels=records, patch_artist=True, showfliers=False)
    colors = plt.cm.Blues(np.linspace(0.35, 0.90, max(len(records), 1)))
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.65)
    rng = np.random.default_rng(20260712)
    for i, values in enumerate(data, start=1):
        if len(values) == 0:
            continue
        sample = values if len(values) <= 120 else rng.choice(values, 120, replace=False)
        x = rng.normal(i, 0.035, size=len(sample))
        ax.scatter(x, sample, s=8, alpha=0.28, color="#222222", linewidths=0)
    ax.set_title("Pulse Arrival Time Distribution")
    ax.set_xlabel("BIDMC record")
    ax.set_ylabel("ECG R-peak to PPG peak delay (ms)")
    ax.tick_params(axis="x", labelrotation=90, labelsize=7)
    ax.grid(True, axis="y", alpha=0.35)
    fig.tight_layout()
    fig.savefig(fig_dir / "fig14_pulse_arrival_time_distribution.png", dpi=300)
    plt.close(fig)


def plot_bland_altman(features: pd.DataFrame, fig_dir: Path) -> None:
    mean_rate = (features["ecg_hr_bpm"] + features["ppg_pr_bpm"]) / 2
    diff = features["ecg_hr_bpm"] - features["ppg_pr_bpm"]
    bias = diff.mean()
    loa = 1.96 * diff.std(ddof=1)
    record_count = features["record_id"].nunique()

    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    if record_count > 12:
        colors = features["record_id"].astype(int)
        sc = ax.scatter(mean_rate, diff, s=24, alpha=0.72, c=colors, cmap="viridis")
        fig.colorbar(sc, ax=ax, label="BIDMC record")
    else:
        for record_id, group in features.groupby("record_id"):
            x = (group["ecg_hr_bpm"] + group["ppg_pr_bpm"]) / 2
            y = group["ecg_hr_bpm"] - group["ppg_pr_bpm"]
            ax.scatter(x, y, s=34, alpha=0.78, label=f"Record {record_id}")
        ax.legend(fontsize=8)
    ax.axhline(bias, color="#222222", linewidth=1.2, label=f"Bias {bias:.2f} bpm")
    ax.axhline(bias + loa, color="#B00020", linestyle="--", linewidth=1.0, label="+1.96 SD")
    ax.axhline(bias - loa, color="#B00020", linestyle="--", linewidth=1.0, label="-1.96 SD")
    ax.set_title("Bland-Altman Analysis of ECG Heart Rate and PPG Pulse Rate")
    ax.set_xlabel("Mean of ECG heart rate and PPG pulse rate (bpm)")
    ax.set_ylabel("ECG heart rate - PPG pulse rate (bpm)")
    ax.grid(True, alpha=0.35)
    fig.tight_layout()
    fig.savefig(fig_dir / "fig15_bland_altman_hr_pr.png", dpi=300)
    plt.close(fig)


def plot_cardiorespiratory_coupling(features: pd.DataFrame, fig_dir: Path) -> None:
    record_count = features["record_id"].nunique()
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    if record_count > 12:
        sc = ax.scatter(
            features["resp_rr_bpm"],
            features["ecg_hr_bpm"],
            s=24,
            alpha=0.72,
            c=features["record_id"].astype(int),
            cmap="viridis",
        )
        fig.colorbar(sc, ax=ax, label="BIDMC record")
    else:
        for record_id, group in features.groupby("record_id"):
            ax.scatter(group["resp_rr_bpm"], group["ecg_hr_bpm"], s=35, alpha=0.75, label=f"Record {record_id}")
    x = features["resp_rr_bpm"].to_numpy()
    y = features["ecg_hr_bpm"].to_numpy()
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() >= 2:
        coef = np.polyfit(x[mask], y[mask], deg=1)
        xx = np.linspace(x[mask].min(), x[mask].max(), 100)
        ax.plot(xx, coef[0] * xx + coef[1], color="#222222", linewidth=1.4, label="Linear fit")
    corr = features["resp_rr_bpm"].corr(features["ecg_hr_bpm"])
    ax.set_title(f"Cardiorespiratory Coupling (r = {corr:.2f})")
    ax.set_xlabel("Respiratory rate (breaths/min)")
    ax.set_ylabel("ECG heart rate (bpm)")
    if record_count <= 12:
        ax.legend(fontsize=8)
    ax.grid(True, alpha=0.35)
    fig.tight_layout()
    fig.savefig(fig_dir / "fig16_cardiorespiratory_coupling.png", dpi=300)
    plt.close(fig)


def plot_fusion_heatmap(summary: pd.DataFrame, fig_dir: Path) -> None:
    metrics = [
        "pat_mean_ms",
        "pat_std_ms",
        "ecg_ppg_rate_corr",
        "ecg_resp_rate_corr",
        "ppg_resp_rate_corr",
    ]
    data = summary.set_index("record_id")[metrics]
    normalized = (data - data.mean()) / data.std(ddof=0)
    normalized = normalized.replace([np.inf, -np.inf], np.nan).fillna(0)

    fig, ax = plt.subplots(figsize=(8.5, max(4.8, len(normalized.index) * 0.18)))
    im = ax.imshow(normalized.to_numpy(), cmap="RdBu_r", vmin=-2, vmax=2, aspect="auto")
    ax.set_xticks(range(len(metrics)), metrics, rotation=35, ha="right")
    ax.set_yticks(range(len(normalized.index)), normalized.index)
    for i in range(normalized.shape[0]):
        for j in range(normalized.shape[1]):
            ax.text(j, i, f"{data.iloc[i, j]:.2f}", ha="center", va="center", fontsize=8)
    ax.set_title("Multimodal Fusion Feature Map")
    fig.colorbar(im, ax=ax, label="Column-wise z-score")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig17_multimodal_fusion_feature_map.png", dpi=300)
    plt.close(fig)


def main_cli() -> None:
    args = parse_args()
    root = project_root()
    fig_dir = root / "figures" / "advanced_fusion"
    fig_dir.mkdir(parents=True, exist_ok=True)

    pat_frames = []
    summary_rows = []
    feature_frames = []
    for record_id in args.records:
        pat, summary = analyze_record(record_id, root)
        pat_frames.append(pat)
        summary_rows.append(summary)
        feature = pd.read_csv(root / "results" / f"{record_id}_features.csv", dtype={"record_id": str})
        feature["record_id"] = record_id
        feature_frames.append(feature)

    pat_all = pd.concat(pat_frames, ignore_index=True)
    summary = pd.DataFrame(summary_rows)
    features = pd.concat(feature_frames, ignore_index=True)

    pat_all.to_csv(root / "results" / "pulse_arrival_times.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(root / "results" / "advanced_fusion_summary.csv", index=False, encoding="utf-8-sig")

    plot_pat_distribution(pat_all, fig_dir)
    plot_bland_altman(features, fig_dir)
    plot_cardiorespiratory_coupling(features, fig_dir)
    plot_fusion_heatmap(summary, fig_dir)

    print("Advanced multimodal fusion analysis complete.")
    print(root / "results" / "advanced_fusion_summary.csv")
    print(fig_dir)


if __name__ == "__main__":
    main_cli()
