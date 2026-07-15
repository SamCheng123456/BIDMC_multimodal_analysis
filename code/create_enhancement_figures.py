from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]


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


def rounded_box(ax, xy, w, h, text, fc="#FFFFFF", ec="#2563EB", tc="#0F172A", size=9):
    patch = FancyBboxPatch(
        xy,
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.04",
        linewidth=1.6,
        edgecolor=ec,
        facecolor=fc,
    )
    ax.add_patch(patch)
    ax.text(
        xy[0] + w / 2,
        xy[1] + h / 2,
        text,
        ha="center",
        va="center",
        color=tc,
        fontsize=size,
        linespacing=1.28,
    )


def arrow(ax, start, end):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=14,
            linewidth=1.4,
            color="#2563EB",
            shrinkA=6,
            shrinkB=6,
        )
    )


def create_workflow() -> None:
    out_dir = ROOT / "figures" / "full_dataset"
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(16.0, 8.0))
    ax.set_xlim(0, 16.0)
    ax.set_ylim(0, 8.0)
    ax.axis("off")
    ax.set_facecolor("#F8FBFF")
    fig.patch.set_facecolor("#F8FBFF")

    ax.text(0.45, 7.55, "全数据集多模态生理信号分析流程", fontsize=18, weight="bold", color="#0F172A")
    ax.text(
        0.45,
        7.18,
        "BIDMC 心电、脉搏波与呼吸信号 | 53 条记录 | 848 个时间窗 | 特征提取与质量控制",
        fontsize=10.5,
        color="#334155",
    )

    boxes = [
        (0.45, 5.75, 2.10, 0.92, "读取 BIDMC 数据\n信号文件与数值记录"),
        (2.95, 5.75, 2.10, 0.92, "选择三种模态\n心电 / 脉搏波 / 呼吸"),
        (5.45, 5.75, 2.10, 0.92, "采样率校验\n125 Hz"),
        (7.95, 5.75, 2.10, 0.92, "带通滤波\n去除基线与高频噪声"),
        (10.45, 5.75, 2.10, 0.92, "Z-score 标准化\n统一幅值尺度"),
        (12.95, 5.75, 2.10, 0.92, "滑动分窗\n30 秒时间窗"),
    ]
    for x, y, w, h, text in boxes:
        rounded_box(ax, (x, y), w, h, text, fc="#FFFFFF", ec="#2563EB", size=9.2)
    for i in range(len(boxes) - 1):
        x, y, w, h, _ = boxes[i]
        nx, ny, nw, nh, _ = boxes[i + 1]
        arrow(ax, (x + w, y + h / 2), (nx, ny + nh / 2))

    lower = [
        (1.00, 3.65, 2.15, 0.95, "峰值检测\n心率 / 脉率 / 呼吸率"),
        (4.00, 3.65, 2.15, 0.95, "FFT 与 STFT\n频域和时频特征"),
        (7.00, 3.65, 2.15, 0.95, "心率变异性特征\nSDNN / RMSSD"),
        (10.00, 3.65, 2.15, 0.95, "多模态融合\nHR-PR / PAT / 耦合"),
        (13.00, 3.65, 2.15, 0.95, "监护仪对照\nHR / PULSE / RESP"),
    ]
    for x, y, w, h, text in lower:
        rounded_box(ax, (x, y), w, h, text, fc="#EFF6FF", ec="#0EA5E9", size=9.0)
    arrow(ax, (14.0, 5.75), (14.08, 4.62))
    for i in range(len(lower) - 1):
        x, y, w, h, _ = lower[i]
        nx, ny, nw, nh, _ = lower[i + 1]
        arrow(ax, (x + w, y + h / 2), (nx, ny + nh / 2))

    outputs = [
        (1.00, 1.25, 2.80, 1.00, "图形结果\n波形、频谱、全数据集图"),
        (4.85, 1.25, 2.80, 1.00, "结果表格\n记录汇总与质量摘要"),
        (8.70, 1.25, 2.80, 1.00, "交互式界面\n记录选择与同步回放"),
        (12.55, 1.25, 2.80, 1.00, "讨论与结论\n可靠性、差异与局限"),
    ]
    for x, y, w, h, text in outputs:
        rounded_box(ax, (x, y), w, h, text, fc="#FFFFFF", ec="#14B8A6", size=8.8)
    arrow(ax, (11.08, 3.65), (2.4, 2.27))
    arrow(ax, (11.08, 3.65), (6.25, 2.27))
    arrow(ax, (11.08, 3.65), (10.1, 2.27))
    arrow(ax, (14.08, 3.65), (13.95, 2.27))

    fig.tight_layout(pad=0.6)
    fig.savefig(out_dir / "fig0_overall_analysis_workflow.png", dpi=300)
    plt.close(fig)


def create_gui_explainer() -> None:
    out_dir = ROOT / "figures" / "gui"
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(13.2, 7.0))
    ax.set_xlim(0, 13.2)
    ax.set_ylim(0, 7.0)
    ax.axis("off")
    ax.set_facecolor("#EAF4FF")
    fig.patch.set_facecolor("#EAF4FF")

    ax.text(0.35, 6.55, "实时多模态信号可视化界面", fontsize=15, weight="bold", color="#0F172A")
    ax.text(0.35, 6.2, "支持记录选择、窗口长度、播放步长、播放/暂停、重置和时间轴拖动", fontsize=9.5, color="#334155")

    # Main software frame
    ax.add_patch(FancyBboxPatch((0.35, 0.45), 8.6, 5.45, boxstyle="round,pad=0.02,rounding_size=0.08", facecolor="#FFFFFF", edgecolor="#1D4ED8", linewidth=1.8))
    ax.add_patch(Rectangle((0.35, 5.35), 8.6, 0.55, facecolor="#1D4ED8", edgecolor="#1D4ED8"))
    ax.text(0.65, 5.63, "BIDMC 多模态回放控制台", color="#FFFFFF", fontsize=10, weight="bold", va="center")
    ax.text(7.25, 5.63, "记录 01 | 40.0-50.0 s", color="#DBEAFE", fontsize=8.5, va="center")

    # Metric cards
    card_x = [0.7, 2.75, 4.8, 6.85]
    card_labels = ["ECG 范围", "PPG 范围", "RESP 范围", "采样率"]
    card_values = ["-1.82 to 2.44", "-1.12 to 1.38", "-1.04 to 1.21", "125 Hz"]
    for x, label, value in zip(card_x, card_labels, card_values):
        ax.add_patch(FancyBboxPatch((x, 4.65), 1.65, 0.48, boxstyle="round,pad=0.02,rounding_size=0.05", facecolor="#EFF6FF", edgecolor="#BFDBFE"))
        ax.text(x + 0.12, 4.97, label, fontsize=7.5, color="#475569")
        ax.text(x + 0.12, 4.78, value, fontsize=8.5, color="#0F172A", weight="bold")

    # Waveform panels
    panel_y = [3.55, 2.45, 1.35]
    panel_names = ["心电 ECG", "脉搏波 PPG", "呼吸 RESP"]
    colors = ["#1D4ED8", "#0284C7", "#0F766E"]
    for y, name, color in zip(panel_y, panel_names, colors):
        ax.add_patch(Rectangle((0.7, y), 7.9, 0.8, facecolor="#F8FAFC", edgecolor="#CBD5E1"))
        ax.text(0.85, y + 0.62, name, fontsize=8.5, color=color, weight="bold")
        xs = np.linspace(1.45, 8.25, 240)
        if "ECG" in name:
            wave = 0.18 * np.sin(xs * 5) + 0.18 * (np.sin(xs * 17) > 0.92)
        elif "PPG" in name:
            wave = 0.22 * np.sin(xs * 3.2 - 0.6) + 0.06 * np.sin(xs * 9)
        else:
            wave = 0.27 * np.sin(xs * 1.2)
        ax.plot(xs, y + 0.4 + wave, color=color, linewidth=1.6)

    # Controls
    ax.add_patch(Rectangle((0.7, 0.72), 7.9, 0.38, facecolor="#EFF6FF", edgecolor="#BFDBFE"))
    ax.text(0.95, 0.91, "播放", fontsize=8.5, color="#1E40AF", va="center")
    ax.text(1.85, 0.91, "暂停", fontsize=8.5, color="#1E40AF", va="center")
    ax.text(2.9, 0.91, "重置", fontsize=8.5, color="#1E40AF", va="center")
    ax.plot([4.1, 8.2], [0.91, 0.91], color="#94A3B8", linewidth=3)
    ax.scatter([5.7], [0.91], s=72, color="#2563EB", zorder=3)

    # Callout boxes
    callouts = [
        (9.55, 4.9, "记录选择", "可在 BIDMC 01-53\n之间切换。"),
        (9.55, 3.75, "播放参数", "窗口长度和步长\n决定时间分辨率。"),
        (9.55, 2.6, "同步视图", "ECG、PPG、RESP\n共用同一时间轴。"),
        (9.55, 1.45, "时间轴控制", "拖动滑块查看\n指定片段和伪迹。"),
        (9.55, 0.55, "工程价值", "把离线分析扩展为\n交互式复核界面。"),
    ]
    for x, y, title, body in callouts:
        ax.add_patch(FancyBboxPatch((x, y), 3.1, 0.72, boxstyle="round,pad=0.02,rounding_size=0.05", facecolor="#FFFFFF", edgecolor="#60A5FA", linewidth=1.2))
        ax.text(x + 0.15, y + 0.49, title, fontsize=8.5, color="#1D4ED8", weight="bold")
        ax.text(x + 0.15, y + 0.18, body, fontsize=7.3, color="#334155")

    fig.tight_layout(pad=0.5)
    fig.savefig(out_dir / "fig_gui_software_explainer.png", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    create_workflow()
    create_gui_explainer()
