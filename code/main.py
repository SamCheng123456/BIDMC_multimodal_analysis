from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.fft import rfft, rfftfreq
from scipy.signal import butter, find_peaks, sosfiltfilt, stft


FS = 125.0
WINDOW_SECONDS = 30

plt.rcParams["font.family"] = ["Times New Roman", "SimSun", "DejaVu Serif"]
plt.rcParams["font.size"] = 10.5
plt.rcParams["axes.unicode_minus"] = False


@dataclass
class RecordData:
    record_id: str
    fs: float
    time: np.ndarray
    ecg: np.ndarray
    ppg: np.ndarray
    resp: np.ndarray


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def ensure_dirs(root: Path) -> None:
    for folder in ["data/raw", "data/processed", "figures", "results"]:
        (root / folder).mkdir(parents=True, exist_ok=True)


def zscore(x: np.ndarray) -> np.ndarray:
    sd = np.nanstd(x)
    if sd == 0 or np.isnan(sd):
        return x - np.nanmean(x)
    return (x - np.nanmean(x)) / sd


def bandpass_filter(x: np.ndarray, fs: float, low: float, high: float, order: int = 4) -> np.ndarray:
    nyq = 0.5 * fs
    sos = butter(order, [low / nyq, high / nyq], btype="band", output="sos")
    return sosfiltfilt(sos, x)


def lowpass_filter(x: np.ndarray, fs: float, cutoff: float, order: int = 4) -> np.ndarray:
    nyq = 0.5 * fs
    sos = butter(order, cutoff / nyq, btype="low", output="sos")
    return sosfiltfilt(sos, x)


def create_demo_record(duration_s: int = 180, fs: float = FS) -> RecordData:
    rng = np.random.default_rng(20260712)
    time = np.arange(0, duration_s, 1 / fs)

    heart_rate_bpm = 76 + 4 * np.sin(2 * np.pi * time / 90)
    rr_s = 60 / heart_rate_bpm
    beat_times = []
    t = 0.5
    while t < duration_s:
        beat_times.append(t)
        t += float(np.interp(t, time, rr_s)) + rng.normal(0, 0.025)

    ecg = 0.02 * rng.normal(size=time.size) + 0.04 * np.sin(2 * np.pi * 0.25 * time)
    for bt in beat_times:
        ecg += 1.25 * np.exp(-0.5 * ((time - bt) / 0.018) ** 2)
        ecg += 0.20 * np.exp(-0.5 * ((time - (bt - 0.16)) / 0.035) ** 2)
        ecg += 0.35 * np.exp(-0.5 * ((time - (bt + 0.25)) / 0.070) ** 2)

    ppg = 0.015 * rng.normal(size=time.size)
    for bt in beat_times:
        delay = 0.22 + rng.normal(0, 0.01)
        pulse_t = time - (bt + delay)
        pulse = np.zeros_like(time)
        mask = pulse_t > 0
        pulse[mask] = (pulse_t[mask] / 0.12) ** 2 * np.exp(-pulse_t[mask] / 0.12)
        ppg += pulse
    ppg = zscore(ppg) * 0.35 + 0.50

    resp_rate_bpm = 17 + 1.5 * np.sin(2 * np.pi * time / 120)
    resp_phase = 2 * np.pi * np.cumsum(resp_rate_bpm / 60) / fs
    resp = 0.55 + 0.35 * np.sin(resp_phase) + 0.03 * rng.normal(size=time.size)

    return RecordData("demo", fs, time, ecg, ppg, resp)


def load_bidmc_csv(raw_dir: Path, record_id: str) -> RecordData:
    path = raw_dir / f"bidmc_{record_id}_Signals.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run code/download_bidmc_csv.py or place BIDMC CSV files in data/raw."
        )

    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]

    def pick(*names: str) -> str:
        lowered = {c.lower(): c for c in df.columns}
        for name in names:
            if name.lower() in lowered:
                return lowered[name.lower()]
        for c in df.columns:
            if any(name.lower() in c.lower() for name in names):
                return c
        raise KeyError(f"Could not find any of these columns: {names}; columns={list(df.columns)}")

    time_col = pick("Time [s]", "time")
    resp_col = pick("RESP", "resp")
    ppg_col = pick("PLETH", "ppg", "pleth")
    ecg_col = pick("II", "ECG", "ekg")

    time = df[time_col].to_numpy(dtype=float)
    duration = float(time[-1] - time[0])
    if duration > 0:
        fs = float((len(time) - 1) / duration)
    else:
        fs = 1.0 / np.median(np.diff(time))
    return RecordData(
        record_id=record_id,
        fs=fs,
        time=time,
        ecg=df[ecg_col].to_numpy(dtype=float),
        ppg=df[ppg_col].to_numpy(dtype=float),
        resp=df[resp_col].to_numpy(dtype=float),
    )


def preprocess(record: RecordData) -> dict[str, np.ndarray]:
    fs = record.fs
    ecg_f = bandpass_filter(record.ecg, fs, 0.5, 40.0)
    ppg_f = bandpass_filter(record.ppg, fs, 0.5, 8.0)
    resp_f = bandpass_filter(record.resp, fs, 0.05, 1.0)
    return {
        "ecg": ecg_f,
        "ppg": ppg_f,
        "resp": resp_f,
        "ecg_z": zscore(ecg_f),
        "ppg_z": zscore(ppg_f),
        "resp_z": zscore(resp_f),
    }


def peak_indices(signal: np.ndarray, fs: float, mode: str) -> np.ndarray:
    if mode == "ecg":
        distance = int(0.35 * fs)
        prominence = max(0.25 * np.std(signal), 0.05)
        peaks, _ = find_peaks(signal, distance=distance, prominence=prominence)
    elif mode == "ppg":
        distance = int(0.40 * fs)
        peaks, _ = find_peaks(signal, distance=distance, prominence=0.25 * np.std(signal))
    elif mode == "resp":
        distance = int(1.5 * fs)
        peaks, _ = find_peaks(signal, distance=distance, prominence=0.20 * np.std(signal))
    else:
        raise ValueError(mode)
    return peaks


def dominant_frequency(signal: np.ndarray, fs: float, low: float, high: float) -> float:
    y = np.abs(rfft(signal - np.mean(signal)))
    f = rfftfreq(signal.size, 1 / fs)
    mask = (f >= low) & (f <= high)
    if not np.any(mask):
        return math.nan
    return float(f[mask][np.argmax(y[mask])])


def interval_features(peaks: np.ndarray, fs: float, scale: float = 60.0) -> dict[str, float]:
    if peaks.size < 3:
        return {"rate_mean": math.nan, "interval_mean_ms": math.nan, "sdnn_ms": math.nan, "rmssd_ms": math.nan}
    intervals_s = np.diff(peaks) / fs
    intervals_ms = intervals_s * 1000
    return {
        "rate_mean": float(scale / np.mean(intervals_s)),
        "interval_mean_ms": float(np.mean(intervals_ms)),
        "sdnn_ms": float(np.std(intervals_ms, ddof=1)),
        "rmssd_ms": float(np.sqrt(np.mean(np.diff(intervals_ms) ** 2))),
    }


def window_features(record: RecordData, clean: dict[str, np.ndarray], root: Path) -> pd.DataFrame:
    rows = []
    win = int(WINDOW_SECONDS * record.fs)
    for start in range(0, len(record.time) - win + 1, win):
        end = start + win
        segment_time = record.time[start:end]
        ecg = clean["ecg"][start:end]
        ppg = clean["ppg"][start:end]
        resp = clean["resp"][start:end]

        ecg_peaks = peak_indices(ecg, record.fs, "ecg")
        ppg_peaks = peak_indices(ppg, record.fs, "ppg")
        resp_peaks = peak_indices(resp, record.fs, "resp")

        ecg_feat = interval_features(ecg_peaks, record.fs)
        ppg_feat = interval_features(ppg_peaks, record.fs)
        resp_feat = interval_features(resp_peaks, record.fs)

        rows.append(
            {
                "record_id": record.record_id,
                "window_start_s": float(segment_time[0]),
                "window_end_s": float(segment_time[-1]),
                "ecg_hr_bpm": ecg_feat["rate_mean"],
                "ppg_pr_bpm": ppg_feat["rate_mean"],
                "resp_rr_bpm": resp_feat["rate_mean"],
                "ecg_sdnn_ms": ecg_feat["sdnn_ms"],
                "ecg_rmssd_ms": ecg_feat["rmssd_ms"],
                "ppg_interval_mean_ms": ppg_feat["interval_mean_ms"],
                "resp_interval_mean_ms": resp_feat["interval_mean_ms"],
                "ecg_rms": float(np.sqrt(np.mean(ecg**2))),
                "ppg_rms": float(np.sqrt(np.mean(ppg**2))),
                "resp_rms": float(np.sqrt(np.mean(resp**2))),
                "ecg_dom_freq_hz": dominant_frequency(ecg, record.fs, 0.6, 3.0),
                "ppg_dom_freq_hz": dominant_frequency(ppg, record.fs, 0.6, 3.0),
                "resp_dom_freq_hz": dominant_frequency(resp, record.fs, 0.05, 0.8),
            }
        )

    df = pd.DataFrame(rows)
    df["hr_pr_abs_error_bpm"] = (df["ecg_hr_bpm"] - df["ppg_pr_bpm"]).abs()
    out = root / "results" / f"{record.record_id}_features.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return df


def save_processed(record: RecordData, clean: dict[str, np.ndarray], root: Path) -> None:
    out = pd.DataFrame(
        {
            "time_s": record.time,
            "ecg_raw": record.ecg,
            "ppg_raw": record.ppg,
            "resp_raw": record.resp,
            "ecg_filtered": clean["ecg"],
            "ppg_filtered": clean["ppg"],
            "resp_filtered": clean["resp"],
            "ecg_z": clean["ecg_z"],
            "ppg_z": clean["ppg_z"],
            "resp_z": clean["resp_z"],
        }
    )
    out.to_csv(root / "data" / "processed" / f"{record.record_id}_processed.csv", index=False, encoding="utf-8-sig")


def plot_all(record: RecordData, clean: dict[str, np.ndarray], feats: pd.DataFrame, root: Path) -> None:
    fs = record.fs
    t = record.time
    max_points = min(len(t), int(60 * fs))
    sl = slice(0, max_points)
    figure_dir = root / "figures" / record.record_id
    figure_dir.mkdir(parents=True, exist_ok=True)

    def out(name: str) -> Path:
        return figure_dir / name

    plt.rcParams.update({"font.size": 10, "axes.grid": True})

    fig, axes = plt.subplots(3, 1, figsize=(10, 7), sharex=True)
    axes[0].plot(t[sl], record.ecg[sl], label="Raw ECG Lead II", color="#2F5E8C")
    axes[1].plot(t[sl], record.ppg[sl], label="Raw PPG/PLETH", color="#B43E4A")
    axes[2].plot(t[sl], record.resp[sl], label="Raw RESP", color="#2F7D59")
    for ax, ylabel in zip(axes, ["ECG amplitude", "PPG amplitude", "RESP amplitude"]):
        ax.set_ylabel(ylabel)
        ax.legend(loc="upper right")
    axes[2].set_xlabel("Time (s)")
    fig.suptitle("Raw ECG, PPG and Respiration Signals")
    fig.tight_layout()
    fig.savefig(out("fig1_raw_multimodal_signals.png"), dpi=300)
    plt.close(fig)

    fig, axes = plt.subplots(3, 1, figsize=(10, 7), sharex=True)
    axes[0].plot(t[sl], clean["ecg"][sl], label="Filtered ECG (0.5-40 Hz)", color="#2F5E8C")
    axes[1].plot(t[sl], clean["ppg"][sl], label="Filtered PPG (0.5-8 Hz)", color="#B43E4A")
    axes[2].plot(t[sl], clean["resp"][sl], label="Filtered RESP (0.05-1 Hz)", color="#2F7D59")
    for ax, ylabel in zip(axes, ["ECG amplitude", "PPG amplitude", "RESP amplitude"]):
        ax.set_ylabel(ylabel)
        ax.legend(loc="upper right")
    axes[2].set_xlabel("Time (s)")
    fig.suptitle("Filtered ECG, PPG and Respiration Signals")
    fig.tight_layout()
    fig.savefig(out("fig2_filtered_multimodal_signals.png"), dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(t[sl], clean["ecg_z"][sl], label="ECG z-score", color="#2F5E8C")
    ax.plot(t[sl], clean["ppg_z"][sl], label="PPG z-score", color="#B43E4A", alpha=0.8)
    ax.plot(t[sl], clean["resp_z"][sl], label="RESP z-score", color="#2F7D59", alpha=0.8)
    ax.set_title("Standardized Multimodal Signals")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Standardized amplitude")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out("fig3_standardized_overlay.png"), dpi=300)
    plt.close(fig)

    ecg_peaks = peak_indices(clean["ecg"], fs, "ecg")
    ppg_peaks = peak_indices(clean["ppg"], fs, "ppg")
    resp_peaks = peak_indices(clean["resp"], fs, "resp")

    def plot_peaks(
        signal_key: str,
        peaks: np.ndarray,
        fig_no: int,
        name: str,
        title: str,
        ylabel: str,
        color: str,
    ) -> None:
        fig, ax = plt.subplots(figsize=(10, 4))
        visible = peaks[peaks < max_points]
        ax.plot(t[sl], clean[signal_key][sl], label=title, color=color)
        ax.scatter(t[visible], clean[signal_key][visible], s=18, color="#111111", label="Detected peaks", zorder=3)
        ax.set_title(name)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel(ylabel)
        ax.legend()
        fig.tight_layout()
        fig.savefig(out(f"fig{fig_no}_{signal_key}_peaks.png"), dpi=300)
        plt.close(fig)

    plot_peaks("ecg", ecg_peaks, 4, "ECG R-Peak Detection", "Filtered ECG", "Amplitude", "#2F5E8C")
    plot_peaks("ppg", ppg_peaks, 5, "PPG Pulse Peak Detection", "Filtered PPG", "Amplitude", "#B43E4A")
    plot_peaks("resp", resp_peaks, 6, "Respiration Peak Detection", "Filtered RESP", "Amplitude", "#2F7D59")

    fig, ax = plt.subplots(figsize=(10, 4))
    for signal_key, label, color, low, high in [
        ("ecg", "ECG", "#2F5E8C", 0.0, 10.0),
        ("ppg", "PPG", "#B43E4A", 0.0, 10.0),
        ("resp", "RESP", "#2F7D59", 0.0, 2.0),
    ]:
        signal = clean[signal_key] - np.mean(clean[signal_key])
        f = rfftfreq(signal.size, 1 / fs)
        y = np.abs(rfft(signal))
        mask = (f >= low) & (f <= high)
        ax.plot(f[mask], y[mask] / np.max(y[mask]), label=label, color=color)
    ax.set_title("Normalized Frequency Spectra")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Normalized magnitude")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out("fig7_frequency_spectra.png"), dpi=300)
    plt.close(fig)

    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    for ax, signal_key, title in zip(axes, ["ecg", "ppg", "resp"], ["ECG", "PPG", "RESP"]):
        f, tt, z = stft(clean[signal_key], fs=fs, nperseg=256, noverlap=128)
        max_f = 12 if signal_key != "resp" else 2
        mask = f <= max_f
        pcm = ax.pcolormesh(tt, f[mask], np.abs(z[mask]), shading="gouraud", cmap="viridis")
        ax.set_ylabel(f"{title}\nHz")
        fig.colorbar(pcm, ax=ax, pad=0.01)
    axes[0].set_title("STFT Time-Frequency Maps")
    axes[-1].set_xlabel("Time (s)")
    fig.tight_layout()
    fig.savefig(out("fig8_stft_time_frequency.png"), dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4))
    x = np.arange(len(feats))
    ax.plot(x, feats["ecg_hr_bpm"], marker="o", label="ECG heart rate", color="#2F5E8C")
    ax.plot(x, feats["ppg_pr_bpm"], marker="s", label="PPG pulse rate", color="#B43E4A")
    ax.plot(x, feats["resp_rr_bpm"], marker="^", label="Respiratory rate", color="#2F7D59")
    ax.set_title("Windowed Vital Sign Estimates")
    ax.set_xlabel(f"Window index ({WINDOW_SECONDS} s/window)")
    ax.set_ylabel("Rate (beats or breaths/min)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out("fig9_windowed_vital_rates.png"), dpi=300)
    plt.close(fig)

    corr_cols = ["ecg_hr_bpm", "ppg_pr_bpm", "resp_rr_bpm", "ecg_sdnn_ms", "ecg_rmssd_ms", "hr_pr_abs_error_bpm"]
    corr = feats[corr_cols].corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(corr, vmin=-1, vmax=1, cmap="coolwarm")
    ax.set_xticks(np.arange(len(corr_cols)), corr_cols, rotation=45, ha="right")
    ax.set_yticks(np.arange(len(corr_cols)), corr_cols)
    for i in range(len(corr_cols)):
        for j in range(len(corr_cols)):
            value = corr.iloc[i, j]
            ax.text(j, i, f"{value:.2f}" if not np.isnan(value) else "NA", ha="center", va="center", fontsize=8)
    ax.set_title("Multimodal Feature Correlation Matrix")
    fig.colorbar(im, ax=ax, label="Pearson correlation")
    fig.tight_layout()
    fig.savefig(out("fig10_feature_correlation_matrix.png"), dpi=300)
    plt.close(fig)


def summarize(feats: pd.DataFrame, root: Path, record_id: str) -> None:
    summary = feats.describe().T
    summary.to_csv(root / "results" / f"{record_id}_feature_summary.csv", encoding="utf-8-sig")

    lines = [
        "# Analysis Summary",
        "",
        f"Record: {record_id}",
        f"Windows: {len(feats)}",
        "",
        "Key feature means:",
        f"- ECG heart rate: {feats['ecg_hr_bpm'].mean():.2f} bpm",
        f"- PPG pulse rate: {feats['ppg_pr_bpm'].mean():.2f} bpm",
        f"- Respiration rate: {feats['resp_rr_bpm'].mean():.2f} breaths/min",
        f"- ECG SDNN: {feats['ecg_sdnn_ms'].mean():.2f} ms",
        f"- ECG RMSSD: {feats['ecg_rmssd_ms'].mean():.2f} ms",
        f"- Mean ECG-PPG rate absolute error: {feats['hr_pr_abs_error_bpm'].mean():.2f} bpm",
    ]
    (root / "results" / f"{record_id}_analysis_summary.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ECG, PPG and respiration multimodal analysis for BIDMC data.")
    parser.add_argument("--record", default="01", help="BIDMC record number, e.g. 01, 02, 03.")
    parser.add_argument("--demo", action="store_true", help="Use simulated ECG/PPG/RESP data for pipeline testing.")
    parser.add_argument("--duration", type=int, default=180, help="Demo signal duration in seconds.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = project_root()
    ensure_dirs(root)

    if args.demo:
        record = create_demo_record(duration_s=args.duration)
    else:
        record = load_bidmc_csv(root / "data" / "raw", args.record)

    clean = preprocess(record)
    save_processed(record, clean, root)
    feats = window_features(record, clean, root)
    plot_all(record, clean, feats, root)
    summarize(feats, root, record.record_id)

    print(f"Analysis complete for record {record.record_id}")
    print(f"Figures: {root / 'figures'}")
    print(f"Results: {root / 'results'}")


if __name__ == "__main__":
    main()
