from __future__ import annotations

import argparse
import math
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import main as single_record


plt.rcParams["font.family"] = ["Times New Roman", "SimSun", "DejaVu Serif"]
plt.rcParams["font.size"] = 10.5
plt.rcParams["axes.unicode_minus"] = False


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def discover_records(raw_dir: Path) -> list[str]:
    records: list[str] = []
    for path in raw_dir.glob("bidmc_*_Signals.csv"):
        parts = path.stem.split("_")
        if len(parts) >= 2 and parts[1].isdigit():
            records.append(parts[1])
    return sorted(set(records), key=lambda x: int(x))


def copy_signals_from_source(source_dir: Path, raw_dir: Path) -> int:
    raw_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for src in sorted(source_dir.glob("bidmc_*_Signals.csv")):
        dst = raw_dir / src.name
        shutil.copy2(src, dst)
        copied += 1
    return copied


def process_record(record_id: str, root: Path, make_plots: bool) -> dict[str, str]:
    try:
        record = single_record.load_bidmc_csv(root / "data" / "raw", record_id)
        clean = single_record.preprocess(record)
        single_record.save_processed(record, clean, root)
        feats = single_record.window_features(record, clean, root)
        single_record.summarize(feats, root, record_id)
        if make_plots:
            single_record.plot_all(record, clean, feats, root)
        return {"record_id": record_id, "status": "ok", "message": "", "windows": str(len(feats))}
    except Exception as exc:  # Keep the full batch running and report failed records.
        return {"record_id": record_id, "status": "failed", "message": repr(exc), "windows": "0"}


def summarize_all(root: Path, records: list[str], report: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = []
    for record_id in records:
        if report.loc[report["record_id"] == record_id, "status"].iloc[0] != "ok":
            continue
        path = root / "results" / f"{record_id}_features.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path, dtype={"record_id": str})
        df["record_id"] = record_id
        frames.append(df)

    if not frames:
        raise RuntimeError("No valid feature tables were generated.")

    all_features = pd.concat(frames, ignore_index=True)
    all_features.to_csv(root / "results" / "all_records_features.csv", index=False, encoding="utf-8-sig")
    all_features.to_csv(root / "results" / "full_dataset_window_features.csv", index=False, encoding="utf-8-sig")

    summary = (
        all_features.groupby("record_id")
        .agg(
            windows=("window_start_s", "count"),
            ecg_hr_mean=("ecg_hr_bpm", "mean"),
            ecg_hr_std=("ecg_hr_bpm", "std"),
            ppg_pr_mean=("ppg_pr_bpm", "mean"),
            ppg_pr_std=("ppg_pr_bpm", "std"),
            resp_rr_mean=("resp_rr_bpm", "mean"),
            resp_rr_std=("resp_rr_bpm", "std"),
            ecg_sdnn_mean=("ecg_sdnn_ms", "mean"),
            ecg_rmssd_mean=("ecg_rmssd_ms", "mean"),
            hr_pr_error_mean=("hr_pr_abs_error_bpm", "mean"),
            hr_pr_error_median=("hr_pr_abs_error_bpm", "median"),
            ecg_dom_freq_mean=("ecg_dom_freq_hz", "mean"),
            ppg_dom_freq_mean=("ppg_dom_freq_hz", "mean"),
            resp_dom_freq_mean=("resp_dom_freq_hz", "mean"),
        )
        .reset_index()
    )
    summary["record_id_num"] = summary["record_id"].astype(int)
    summary = summary.sort_values("record_id_num").drop(columns=["record_id_num"])
    summary.to_csv(root / "results" / "all_records_summary.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(root / "results" / "full_dataset_record_summary.csv", index=False, encoding="utf-8-sig")
    return all_features, summary


def finite_values(series: pd.Series) -> np.ndarray:
    values = series.to_numpy(dtype=float)
    return values[np.isfinite(values)]


def plot_full_dataset(all_features: pd.DataFrame, summary: pd.DataFrame, root: Path) -> None:
    fig_dir = root / "figures" / "full_dataset"
    fig_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 9, "axes.grid": True})

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    metrics = [
        ("ecg_hr_bpm", "ECG heart rate", "bpm", "#2563EB"),
        ("ppg_pr_bpm", "PPG pulse rate", "bpm", "#0EA5E9"),
        ("resp_rr_bpm", "Respiratory rate", "breaths/min", "#14B8A6"),
    ]
    for ax, (col, title, unit, color) in zip(axes, metrics):
        vals = finite_values(all_features[col])
        ax.hist(vals, bins=28, color=color, alpha=0.82, edgecolor="white")
        ax.axvline(np.nanmean(vals), color="#111827", linewidth=1.3, label=f"Mean {np.nanmean(vals):.2f}")
        ax.set_title(title)
        ax.set_xlabel(unit)
        ax.set_ylabel("Window count")
        ax.legend(fontsize=8)
    fig.suptitle("Full-Dataset Vital Sign Distributions")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig19_full_dataset_vital_sign_distributions.png", dpi=300)
    plt.close(fig)

    ranked = summary.sort_values("hr_pr_error_mean", ascending=False)
    fig_height = max(7.0, len(ranked) * 0.14)
    fig, ax = plt.subplots(figsize=(10, fig_height))
    colors = np.where(ranked["hr_pr_error_mean"] >= ranked["hr_pr_error_mean"].median(), "#2563EB", "#93C5FD")
    y = np.arange(len(ranked))
    ax.barh(y, ranked["hr_pr_error_mean"], color=colors)
    ax.set_yticks(y, ranked["record_id"].astype(str))
    ax.invert_yaxis()
    ax.set_title("Ranked ECG-PPG Rate Difference Across 53 Records")
    ax.set_xlabel("Mean absolute HR-PR error (bpm)")
    ax.set_ylabel("BIDMC record")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig20_ranked_hr_pr_error_all_records.png", dpi=300)
    plt.close(fig)

    corr_cols = [
        "ecg_hr_bpm",
        "ppg_pr_bpm",
        "resp_rr_bpm",
        "ecg_sdnn_ms",
        "ecg_rmssd_ms",
        "hr_pr_abs_error_bpm",
        "ecg_dom_freq_hz",
        "ppg_dom_freq_hz",
        "resp_dom_freq_hz",
    ]
    corr = all_features[corr_cols].corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(corr, vmin=-1, vmax=1, cmap="RdBu_r")
    ax.set_xticks(range(len(corr_cols)), corr_cols, rotation=45, ha="right")
    ax.set_yticks(range(len(corr_cols)), corr_cols)
    for i in range(len(corr_cols)):
        for j in range(len(corr_cols)):
            value = corr.iloc[i, j]
            ax.text(j, i, "NA" if math.isnan(value) else f"{value:.2f}", ha="center", va="center", fontsize=7)
    ax.set_title("Full-Dataset Multimodal Feature Correlation")
    fig.colorbar(im, ax=ax, label="Pearson correlation")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig21_full_dataset_feature_correlation.png", dpi=300)
    plt.close(fig)

    heat_cols = ["ecg_hr_mean", "ppg_pr_mean", "resp_rr_mean", "ecg_sdnn_mean", "ecg_rmssd_mean", "hr_pr_error_mean"]
    data = summary.set_index("record_id")[heat_cols].copy()
    normalized = (data - data.mean()) / data.std(ddof=0)
    normalized = normalized.replace([np.inf, -np.inf], np.nan).fillna(0)
    fig, ax = plt.subplots(figsize=(8.5, max(8.0, len(data) * 0.18)))
    im = ax.imshow(normalized.to_numpy(), cmap="RdBu_r", vmin=-2.5, vmax=2.5, aspect="auto")
    ax.set_xticks(range(len(heat_cols)), heat_cols, rotation=35, ha="right")
    ax.set_yticks(range(len(data.index)), data.index.astype(str))
    ax.set_title("Full-Dataset Record-Level Feature Map")
    fig.colorbar(im, ax=ax, label="Column-wise z-score")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig22_full_dataset_record_feature_map.png", dpi=300)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run BIDMC multimodal analysis on all available records.")
    parser.add_argument("--source-dir", type=Path, help="Optional BIDMC bidmc_csv folder; copies *_Signals.csv into data/raw.")
    parser.add_argument("--records", nargs="*", help="Specific record numbers. Omit to process all discovered records.")
    parser.add_argument("--with-record-plots", action="store_true", help="Also generate the 10 per-record figures for every record.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = project_root()
    single_record.ensure_dirs(root)

    raw_dir = root / "data" / "raw"
    if args.source_dir:
        copied = copy_signals_from_source(args.source_dir, raw_dir)
        print(f"Copied {copied} signal files from {args.source_dir}")

    records = args.records or discover_records(raw_dir)
    records = sorted(set(records), key=lambda x: int(x))
    if not records:
        raise RuntimeError("No BIDMC signal files found in data/raw.")

    report_rows = []
    for index, record_id in enumerate(records, start=1):
        print(f"[{index:02d}/{len(records):02d}] Processing record {record_id}...")
        report_rows.append(process_record(record_id, root, make_plots=args.with_record_plots))

    report = pd.DataFrame(report_rows)
    report.to_csv(root / "results" / "full_dataset_processing_report.csv", index=False, encoding="utf-8-sig")
    ok_records = report.loc[report["status"] == "ok", "record_id"].tolist()
    all_features, summary = summarize_all(root, ok_records, report)
    plot_full_dataset(all_features, summary, root)

    print("Full-dataset analysis complete.")
    print(f"Successful records: {len(ok_records)}/{len(records)}")
    print(root / "results" / "full_dataset_record_summary.csv")
    print(root / "figures" / "full_dataset")


if __name__ == "__main__":
    main()
