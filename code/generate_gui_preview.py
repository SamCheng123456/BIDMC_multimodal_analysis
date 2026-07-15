from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import pandas as pd


BG = "#F4F8FF"
PANEL = "#FFFFFF"
PRIMARY = "#0B63CE"
PRIMARY_DARK = "#073B78"
CYAN = "#18A6D9"
NAVY = "#153E75"
MUTED = "#5D728A"
GRID = "#D8E6F7"


plt.rcParams["font.sans-serif"] = [
    "SimSun",
    "宋体",
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "Arial Unicode MS",
    "DejaVu Sans",
]
plt.rcParams["font.size"] = 10.5
plt.rcParams["axes.unicode_minus"] = False


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成论文用 GUI 预览图。")
    parser.add_argument("--record", default="01")
    parser.add_argument("--start", type=float, default=40.0)
    parser.add_argument("--window", type=float, default=10.0)
    return parser.parse_args()


def rounded(ax, xy, width, height, color, radius=0.025, ec="#D8E6F7", lw=1.0):
    patch = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle=f"round,pad=0.012,rounding_size={radius}",
        linewidth=lw,
        edgecolor=ec,
        facecolor=color,
    )
    ax.add_patch(patch)
    return patch


def main() -> None:
    args = parse_args()
    root = project_root()
    df = pd.read_csv(root / "data" / "processed" / f"{args.record}_processed.csv")
    chunk = df[(df["time_s"] >= args.start) & (df["time_s"] <= args.start + args.window)]

    out_dir = root / "figures" / "gui"
    out_dir.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(13, 7.6), facecolor=BG)
    canvas = fig.add_axes([0, 0, 1, 1])
    canvas.axis("off")

    rounded(canvas, (0.035, 0.885), 0.93, 0.085, PRIMARY_DARK, radius=0.018, ec=PRIMARY_DARK)
    canvas.text(0.06, 0.935, "BIDMC 多模态生命体征查看器", color="white", fontsize=20, fontweight="bold", va="center")
    canvas.text(0.06, 0.902, f"记录 {args.record} | ECG + PPG + 呼吸信号同步回放", color="#BFD7FF", fontsize=10)
    canvas.text(0.83, 0.92, f"{args.start:.2f}s - {args.start + args.window:.2f}s", color="#DCEBFF", fontsize=11, ha="center")

    metrics = [
        ("心电 ECG 动态范围", "3.72", "z-score"),
        ("脉搏波 PPG 动态范围", "2.45", "z-score"),
        ("呼吸 RESP 动态范围", "2.94", "z-score"),
        ("采样率", "125", "Hz"),
    ]
    for i, (label, value, unit) in enumerate(metrics):
        x = 0.035 + i * 0.235
        rounded(canvas, (x, 0.765), 0.215, 0.085, PANEL, radius=0.018)
        canvas.text(x + 0.018, 0.823, label, color=MUTED, fontsize=9)
        canvas.text(x + 0.018, 0.785, value, color=PRIMARY_DARK, fontsize=21, fontweight="bold")
        canvas.text(x + 0.083, 0.79, unit, color=MUTED, fontsize=9)

    rounded(canvas, (0.035, 0.145), 0.93, 0.59, PANEL, radius=0.018)
    labels = [
        ("ecg_z", "心电 ECG", "#0B63CE"),
        ("ppg_z", "脉搏波 PPG", "#18A6D9"),
        ("resp_z", "呼吸 RESP", "#153E75"),
    ]
    y_positions = [0.575, 0.375, 0.175]
    for (column, label, color), bottom in zip(labels, y_positions):
        ax = fig.add_axes([0.09, bottom, 0.83, 0.145], facecolor="#FBFDFF")
        ax.plot(chunk["time_s"], chunk[column], color=color, linewidth=1.3)
        ax.fill_between(chunk["time_s"], chunk[column], 0, color=color, alpha=0.08)
        ax.set_title(label, loc="left", fontsize=11, fontweight="bold", color=PRIMARY_DARK, pad=2)
        ax.set_ylabel("z-score", fontsize=8, color=PRIMARY_DARK)
        ax.grid(True, color=GRID, linewidth=0.8)
        ax.tick_params(colors=MUTED, labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("#C9DDF5")
        if label != "RESP":
            ax.set_xticklabels([])
        else:
            ax.set_xlabel("时间 (s)", color=PRIMARY_DARK, fontsize=9)

    rounded(canvas, (0.035, 0.045), 0.93, 0.065, BG, radius=0.016, ec="#C9DDF5")
    rounded(canvas, (0.055, 0.062), 0.075, 0.032, PRIMARY, radius=0.014, ec=PRIMARY)
    canvas.text(0.092, 0.078, "播放", color="white", fontsize=10, fontweight="bold", ha="center", va="center")
    rounded(canvas, (0.142, 0.062), 0.075, 0.032, "#EAF3FF", radius=0.014, ec="#C9DDF5")
    canvas.text(0.179, 0.078, "重置", color=PRIMARY_DARK, fontsize=10, ha="center", va="center")
    canvas.text(0.245, 0.078, "时间轴", color=PRIMARY_DARK, fontsize=10, va="center")
    canvas.add_patch(Rectangle((0.315, 0.075), 0.55, 0.008, color="#D6E8FF"))
    canvas.add_patch(Rectangle((0.315, 0.075), 0.19, 0.008, color=PRIMARY))
    canvas.scatter([0.505], [0.079], s=110, color=PRIMARY, edgecolor="white", linewidth=1.5, zorder=5)

    out = out_dir / "fig18_gui_preview.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    main()
