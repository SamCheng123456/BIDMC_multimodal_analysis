from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate feature tables from multiple BIDMC records.")
    parser.add_argument("--records", nargs="+", default=["01", "02", "03"], help="Record numbers to aggregate.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = project_root()
    frames = []
    for record in args.records:
        path = root / "results" / f"{record}_features.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing {path}. Run python code/main.py --record {record} first.")
        df = pd.read_csv(path, dtype={"record_id": str})
        df["record_id"] = record
        frames.append(df)

    all_features = pd.concat(frames, ignore_index=True)
    all_features.to_csv(root / "results" / "all_records_features.csv", index=False, encoding="utf-8-sig")

    summary = (
        all_features.groupby("record_id")
        .agg(
            ecg_hr_mean=("ecg_hr_bpm", "mean"),
            ecg_hr_std=("ecg_hr_bpm", "std"),
            ppg_pr_mean=("ppg_pr_bpm", "mean"),
            ppg_pr_std=("ppg_pr_bpm", "std"),
            resp_rr_mean=("resp_rr_bpm", "mean"),
            resp_rr_std=("resp_rr_bpm", "std"),
            ecg_sdnn_mean=("ecg_sdnn_ms", "mean"),
            ecg_rmssd_mean=("ecg_rmssd_ms", "mean"),
            hr_pr_error_mean=("hr_pr_abs_error_bpm", "mean"),
            windows=("window_start_s", "count"),
        )
        .reset_index()
    )
    summary.to_csv(root / "results" / "all_records_summary.csv", index=False, encoding="utf-8-sig")

    fig_dir = root / "figures" / "all_records"
    fig_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.grid": True})

    x = range(len(summary))
    labels = summary["record_id"].astype(str).tolist()

    fig, ax = plt.subplots(figsize=(9, 5))
    width = 0.25
    ax.bar([i - width for i in x], summary["ecg_hr_mean"], width=width, yerr=summary["ecg_hr_std"], label="ECG HR")
    ax.bar(x, summary["ppg_pr_mean"], width=width, yerr=summary["ppg_pr_std"], label="PPG PR")
    ax.bar([i + width for i in x], summary["resp_rr_mean"], width=width, yerr=summary["resp_rr_std"], label="RESP RR")
    ax.set_xticks(list(x), labels)
    ax.set_title("Cross-Record Vital Sign Comparison")
    ax.set_xlabel("BIDMC record")
    ax.set_ylabel("Rate (beats or breaths/min)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(fig_dir / "fig11_cross_record_vital_signs.png", dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(labels, summary["hr_pr_error_mean"], color="#785EF0")
    ax.set_title("ECG Heart Rate and PPG Pulse Rate Difference")
    ax.set_xlabel("BIDMC record")
    ax.set_ylabel("Mean absolute error (bpm)")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig12_hr_pr_error_comparison.png", dpi=300)
    plt.close(fig)

    corr_cols = ["ecg_hr_bpm", "ppg_pr_bpm", "resp_rr_bpm", "ecg_sdnn_ms", "ecg_rmssd_ms", "hr_pr_abs_error_bpm"]
    corr = all_features[corr_cols].corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(corr, vmin=-1, vmax=1, cmap="coolwarm")
    ax.set_xticks(range(len(corr_cols)), corr_cols, rotation=45, ha="right")
    ax.set_yticks(range(len(corr_cols)), corr_cols)
    for i in range(len(corr_cols)):
        for j in range(len(corr_cols)):
            value = corr.iloc[i, j]
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=8)
    ax.set_title("Cross-Record Feature Correlation Matrix")
    fig.colorbar(im, ax=ax, label="Pearson correlation")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig13_cross_record_feature_correlation.png", dpi=300)
    plt.close(fig)

    print("Aggregate analysis complete.")
    print(root / "results" / "all_records_summary.csv")
    print(fig_dir)


if __name__ == "__main__":
    main()
