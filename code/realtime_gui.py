from __future__ import annotations

import argparse
import tkinter as tk
from pathlib import Path
from tkinter import ttk

import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


BG = "#F4F8FF"
PANEL = "#FFFFFF"
PRIMARY = "#0B63CE"
PRIMARY_DARK = "#073B78"
LINE_BLUE = "#0B63CE"
LINE_CYAN = "#18A6D9"
LINE_NAVY = "#153E75"
MUTED = "#5D728A"
GRID = "#D8E6F7"


plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "Arial Unicode MS",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ECG/PPG/RESP 多模态生命体征实时回放界面。")
    parser.add_argument("--record", default="01", help="处理后的记录编号，例如 01、02、03。")
    parser.add_argument("--window", type=float, default=10.0, help="显示窗口长度，单位为秒。")
    parser.add_argument("--step", type=float, default=0.25, help="播放步长，单位为秒。")
    return parser.parse_args()


def metric_text(df: pd.DataFrame) -> tuple[str, str, str]:
    # Approximate dashboard values from the loaded processed signal. The formal
    # numerical analysis still comes from results/*.csv.
    ecg_range = df["ecg_z"].quantile(0.95) - df["ecg_z"].quantile(0.05)
    ppg_range = df["ppg_z"].quantile(0.95) - df["ppg_z"].quantile(0.05)
    resp_range = df["resp_z"].quantile(0.95) - df["resp_z"].quantile(0.05)
    return f"{ecg_range:.2f}", f"{ppg_range:.2f}", f"{resp_range:.2f}"


class RealtimeViewer:
    def __init__(self, root: tk.Tk, df: pd.DataFrame, record_id: str, window_s: float, step_s: float) -> None:
        self.root = root
        self.df = df
        self.record_id = record_id
        self.window_s = window_s
        self.step_s = step_s
        self.running = False
        self.start_s = float(df["time_s"].min())
        self.max_s = float(df["time_s"].max() - window_s)

        root.title(f"BIDMC 多模态生命体征查看器 - 记录 {record_id}")
        root.geometry("1220x820")
        root.configure(bg=BG)
        self.configure_style()

        shell = ttk.Frame(root, style="Shell.TFrame", padding=16)
        shell.pack(fill=tk.BOTH, expand=True)

        self.build_header(shell)
        self.build_metrics(shell)
        self.build_chart(shell)
        self.build_controls(shell)
        self.draw()

    def configure_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Shell.TFrame", background=BG)
        style.configure("Header.TFrame", background=PRIMARY_DARK)
        style.configure("Panel.TFrame", background=PANEL, relief="flat")
        style.configure("Metric.TFrame", background=PANEL, relief="flat")
        style.configure("HeaderTitle.TLabel", background=PRIMARY_DARK, foreground="#FFFFFF", font=("Segoe UI", 18, "bold"))
        style.configure("HeaderSub.TLabel", background=PRIMARY_DARK, foreground="#BFD7FF", font=("Segoe UI", 10))
        style.configure("MetricLabel.TLabel", background=PANEL, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("MetricValue.TLabel", background=PANEL, foreground=PRIMARY_DARK, font=("Segoe UI", 18, "bold"))
        style.configure("Control.TLabel", background=BG, foreground=PRIMARY_DARK, font=("Segoe UI", 10))
        style.configure("Accent.TButton", background=PRIMARY, foreground="#FFFFFF", font=("Segoe UI", 10, "bold"), padding=(16, 8))
        style.map("Accent.TButton", background=[("active", "#0954AD")])
        style.configure("Ghost.TButton", background="#EAF3FF", foreground=PRIMARY_DARK, font=("Segoe UI", 10), padding=(14, 8))
        style.map("Ghost.TButton", background=[("active", "#DCEBFF")])
        style.configure("Horizontal.TScale", background=BG, troughcolor="#D6E8FF")

    def build_header(self, parent: ttk.Frame) -> None:
        header = ttk.Frame(parent, style="Header.TFrame", padding=(18, 14))
        header.pack(fill=tk.X)
        left = ttk.Frame(header, style="Header.TFrame")
        left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(left, text="BIDMC 多模态生命体征查看器", style="HeaderTitle.TLabel").pack(anchor="w")
        ttk.Label(
            left,
            text=f"记录 {self.record_id} | ECG + PPG + 呼吸信号同步回放",
            style="HeaderSub.TLabel",
        ).pack(anchor="w", pady=(4, 0))
        self.status = tk.StringVar(value="")
        ttk.Label(header, textvariable=self.status, style="HeaderSub.TLabel").pack(side=tk.RIGHT)

    def build_metrics(self, parent: ttk.Frame) -> None:
        metrics = ttk.Frame(parent, style="Shell.TFrame")
        metrics.pack(fill=tk.X, pady=(14, 14))
        values = metric_text(self.df)
        cards = [
            ("心电 ECG 动态范围", values[0], "z-score"),
            ("脉搏波 PPG 动态范围", values[1], "z-score"),
            ("呼吸 RESP 动态范围", values[2], "z-score"),
            ("采样率", "125", "Hz"),
        ]
        for i, (label, value, unit) in enumerate(cards):
            card = ttk.Frame(metrics, style="Metric.TFrame", padding=(16, 12))
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 10, 0))
            metrics.columnconfigure(i, weight=1)
            ttk.Label(card, text=label, style="MetricLabel.TLabel").pack(anchor="w")
            line = ttk.Frame(card, style="Metric.TFrame")
            line.pack(anchor="w", pady=(3, 0))
            ttk.Label(line, text=value, style="MetricValue.TLabel").pack(side=tk.LEFT)
            ttk.Label(line, text="  " + unit, style="MetricLabel.TLabel").pack(side=tk.LEFT, pady=(8, 0))

    def build_chart(self, parent: ttk.Frame) -> None:
        chart_panel = ttk.Frame(parent, style="Panel.TFrame", padding=(12, 12))
        chart_panel.pack(fill=tk.BOTH, expand=True)
        self.fig, self.axes = plt.subplots(3, 1, figsize=(11.2, 6.6), sharex=True)
        self.fig.patch.set_facecolor(PANEL)
        self.fig.subplots_adjust(hspace=0.24, left=0.08, right=0.98, top=0.94, bottom=0.10)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def build_controls(self, parent: ttk.Frame) -> None:
        controls = ttk.Frame(parent, style="Shell.TFrame", padding=(0, 12, 0, 0))
        controls.pack(fill=tk.X)
        self.play_button = ttk.Button(controls, text="播放", style="Accent.TButton", command=self.toggle)
        self.play_button.pack(side=tk.LEFT)
        ttk.Button(controls, text="重置", style="Ghost.TButton", command=self.reset).pack(side=tk.LEFT, padx=(10, 18))
        ttk.Label(controls, text="时间轴", style="Control.TLabel").pack(side=tk.LEFT, padx=(0, 8))
        self.position = tk.DoubleVar(value=self.start_s)
        self.slider = ttk.Scale(
            controls,
            from_=self.start_s,
            to=self.max_s,
            orient=tk.HORIZONTAL,
            variable=self.position,
            command=lambda _value: self.draw(),
        )
        self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def toggle(self) -> None:
        self.running = not self.running
        self.play_button.configure(text="暂停" if self.running else "播放")
        if self.running:
            self.tick()

    def reset(self) -> None:
        self.running = False
        self.play_button.configure(text="播放")
        self.position.set(self.start_s)
        self.draw()

    def tick(self) -> None:
        if not self.running:
            return
        next_pos = self.position.get() + self.step_s
        if next_pos >= self.max_s:
            next_pos = self.start_s
        self.position.set(next_pos)
        self.draw()
        self.root.after(80, self.tick)

    def draw(self) -> None:
        start = self.position.get()
        end = start + self.window_s
        chunk = self.df[(self.df["time_s"] >= start) & (self.df["time_s"] <= end)]

        labels = [
            ("ecg_z", "心电 ECG", "标准化幅值", LINE_BLUE),
            ("ppg_z", "脉搏波 PPG", "标准化幅值", LINE_CYAN),
            ("resp_z", "呼吸 RESP", "标准化幅值", LINE_NAVY),
        ]
        for ax, (column, label, ylabel, color) in zip(self.axes, labels):
            ax.clear()
            ax.set_facecolor("#FBFDFF")
            ax.plot(chunk["time_s"], chunk[column], color=color, linewidth=1.35)
            ax.fill_between(chunk["time_s"], chunk[column], 0, color=color, alpha=0.07)
            ax.set_ylabel(ylabel, color=PRIMARY_DARK, fontsize=9)
            ax.set_title(label, loc="left", color=PRIMARY_DARK, fontsize=11, fontweight="bold", pad=6)
            ax.grid(True, color=GRID, linewidth=0.8)
            ax.tick_params(colors=MUTED, labelsize=8)
            for spine in ax.spines.values():
                spine.set_color("#C9DDF5")
        self.axes[-1].set_xlabel("时间 (s)", color=PRIMARY_DARK)
        self.status.set(f"{start:6.2f} s - {end:6.2f} s")
        self.canvas.draw_idle()


def main() -> None:
    args = parse_args()
    path = project_root() / "data" / "processed" / f"{args.record}_processed.csv"
    if not path.exists():
        raise FileNotFoundError(f"未找到 {path}。请先运行 python code/main.py --record {args.record}。")
    df = pd.read_csv(path)
    tk_root = tk.Tk()
    RealtimeViewer(tk_root, df, args.record, args.window, args.step)
    tk_root.mainloop()


if __name__ == "__main__":
    main()
