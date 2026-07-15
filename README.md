# ECG、PPG 与呼吸信号多模态生命体征分析

本项目用于课程论文题目：

**基于 ECG、PPG 与呼吸信号的多模态生命体征特征提取与分析**

推荐数据集为 PhysioNet 的 **BIDMC PPG and Respiration Dataset v1.0.0**。该数据集包含 ECG、PPG/PLETH、阻抗呼吸信号、生命体征数值和人工呼吸标注，适合完成多模态生理信号分析课程论文。

## 目录结构

```text
BIDMC_multimodal_analysis/
├── code/
│   ├── main.py
│   ├── run_all_records.py
│   ├── compare_with_numerics.py
│   └── download_bidmc_csv.py
├── data/
│   ├── raw/
│   └── processed/
├── figures/
├── results/
├── docs/
├── requirements.txt
└── README.md
```

## 环境安装

```bash
pip install -r requirements.txt
```

## 先跑通演示数据

如果还没有下载真实 BIDMC 数据，可以先运行仿真模式，检查预处理、特征提取和绘图流程：

```bash
python code/main.py --demo
```

运行后会生成：

- `figures/`：10 幅课程论文可用图表。
- `results/demo_features.csv`：分窗特征表。
- `results/demo_feature_summary.csv`：统计摘要。
- `data/processed/demo_processed.csv`：处理后数据。

## 下载真实 BIDMC 数据

自动下载 3 条记录：

```bash
python code/download_bidmc_csv.py --records 01 02 03
```

如果命令行下载被 PhysioNet 拦截，可以手动打开：

https://physionet.org/content/bidmc/1.0.0/bidmc_csv/

下载以下文件并放入 `data/raw/`：

```text
bidmc_01_Signals.csv
bidmc_01_Numerics.csv
bidmc_01_Breaths.csv
bidmc_01_Fix.txt
```

至少需要 `bidmc_01_Signals.csv` 才能运行主分析。

## 运行真实数据分析

```bash
python code/main.py --record 01
```

如需分析其他记录：

```bash
python code/main.py --record 02
python code/main.py --record 03
```

## 运行完整 53 条记录分析

本项目已经支持处理 BIDMC CSV 目录中的全部 53 条记录。若完整数据集已下载到本机，可先将
`bidmc_*_Signals.csv` 和 `bidmc_*_Numerics.csv` 放入 `data/raw/`，或直接运行：

```bash
python code/run_all_records.py --source-dir "D:\Users\lenovo\Downloads\bidmc-ppg-and-respiration-dataset-1.0.0\bidmc-ppg-and-respiration-dataset-1.0.0\bidmc_csv"
python code/advanced_fusion_analysis.py --records 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53
python code/compare_with_numerics.py
```

全量分析会生成：

- `results/full_dataset_window_features.csv`：53 条记录、848 个 30 s 窗口的信号特征。
- `results/full_dataset_record_summary.csv`：记录级统计摘要。
- `results/full_dataset_monitor_comparison.csv`：信号估计值与官方 Numerics 的窗口级对比。
- `results/full_dataset_monitor_comparison_summary.csv`：记录级质量控制摘要。
- `figures/full_dataset/`：全数据集分布图、误差排序图、特征相关图和质量控制图。

## 已实现的课程要求

- 数据预处理：ECG 0.5-40 Hz 带通滤波，PPG 0.5-8 Hz 带通滤波，RESP 0.05-1 Hz 带通滤波，三路信号标准化。
- 分析方法：时域峰值检测、频域 FFT、时频 STFT。
- 特征提取：心率、脉率、呼吸率、RR/脉搏/呼吸间期、SDNN、RMSSD、RMS、主频率。
- 多模态分析：ECG 心率与 PPG 脉率误差，生命体征分窗趋势，特征相关性矩阵。
- 全数据集扩展：已处理 BIDMC 全部 53 条记录，并引入 Numerics 监护仪数值进行质量控制对比。
- 可视化：默认导出 10 幅图，满足任务书“不少于 8 幅”的要求。

## 数据集引用

论文中建议引用：

Pimentel M A F, Johnson A E W, Charlton P H, et al. Towards a robust estimation of respiratory rate from pulse oximeters[J]. IEEE Transactions on Biomedical Engineering, 2017, 64(8): 1914-1923.

Goldberger A L, Amaral L A N, Glass L, et al. PhysioBank, PhysioToolkit, and PhysioNet: Components of a new research resource for complex physiologic signals[J]. Circulation, 2000, 101(23): e215-e220.

## 加分项扩展分析

完成基础分析后，可运行以下命令生成多模态融合扩展结果：

```bash
python code/aggregate_records.py --records 01 02 03
python code/advanced_fusion_analysis.py --records 01 02 03
```

扩展分析包括 ECG-PPG 一致性分析、ECG-PPG 峰值时延估计、心肺耦合分析和多模态融合特征热图。详细说明见：

```text
docs/bonus_implementation.md
```

## 实时可视化 GUI

运行以下命令可打开三模态信号实时回放界面：

```bash
python code/realtime_gui.py --record 01
```

可选参数示例：

```bash
python code/realtime_gui.py --record 01 --window 10 --step 0.25
```

界面包含顶部状态栏、生命体征指标卡片、三路同步波形区和时间轴控制区。论文展示图可通过以下命令生成：

```bash
python code/generate_gui_preview.py --record 01 --start 40 --window 10
```

生成结果：

```text
figures/gui/fig18_gui_preview.png
```

## GitHub 项目管理

本项目提供适合上传 GitHub 的轻量版仓库结构。仓库保留核心代码、结果表、论文图表和说明文档；原始 BIDMC 全量数据不建议直接上传至 GitHub，数据来源和获取方式见 `DATA.md`。

推荐查看提交记录：

```bash
git log --oneline --decorate
```

提交历史按以下模块组织：

- `chore`：初始化项目结构、依赖和忽略规则。
- `feat`：实现数据读取、预处理、特征提取、全数据集分析、多模态融合和 GUI。
- `docs`：补充论文、图表、数据说明和 Git 项目管理说明。
- `results`：保存可复现实验统计结果和论文图表。

更详细的提交组织说明见 `GIT_HISTORY.md`。
