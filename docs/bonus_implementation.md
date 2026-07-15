# 加分项实现说明

本项目在基础课程要求之外，选择实现了性价比较高、容易在论文中合理展开的加分项。

## 已实现的加分项

### 1. 多模态数据融合

已实现。项目不是分别孤立分析 ECG、PPG 和 RESP，而是进行了跨模态联合分析：

- ECG 心率与 PPG 脉率对比。
- ECG 心率与 PPG 脉率绝对误差分析。
- ECG、PPG、RESP 分窗生命体征趋势比较。
- 多模态特征相关性矩阵。
- ECG-PPG 峰值时延估计，用于描述心电活动与外周脉搏波之间的时间关系。
- ECG 心率、PPG 脉率与呼吸率之间的心肺耦合分析。

对应代码：

```bash
python code/main.py --record 01
python code/main.py --record 02
python code/main.py --record 03
python code/aggregate_records.py --records 01 02 03
python code/advanced_fusion_analysis.py --records 01 02 03
```

对应结果：

- `results/all_records_summary.csv`
- `results/advanced_fusion_summary.csv`
- `results/pulse_arrival_times.csv`

对应图表：

- `figures/all_records/fig11_cross_record_vital_signs.png`
- `figures/all_records/fig12_hr_pr_error_comparison.png`
- `figures/all_records/fig13_cross_record_feature_correlation.png`
- `figures/advanced_fusion/fig14_pulse_arrival_time_distribution.png`
- `figures/advanced_fusion/fig15_bland_altman_hr_pr.png`
- `figures/advanced_fusion/fig16_cardiorespiratory_coupling.png`
- `figures/advanced_fusion/fig17_multimodal_fusion_feature_map.png`

论文中建议写法：

> 为体现多模态融合思想，本文不仅分别提取 ECG、PPG 和 RESP 特征，还进一步比较 ECG 心率与 PPG 脉率的一致性，估计 ECG R 峰与 PPG 脉搏峰之间的时间延迟，并分析心率、脉率与呼吸率之间的相关关系。

注意：本文中的 ECG-PPG 峰值时延为信号处理层面的时间延迟估计，不应严格等同于临床标准脉搏传导时间。

## 2. 实时可视化界面 / GUI 设计

已实现。项目提供了一个轻量级实时回放界面，用于动态显示 ECG、PPG 和 RESP 三路信号。

运行方式：

```bash
python code/realtime_gui.py --record 01
```

界面功能：

- 同步显示 ECG、PPG、RESP 三路标准化信号。
- 支持播放、暂停、重置。
- 支持通过滑动条查看不同时间段。
- 支持设定显示窗口长度和播放步长。

示例：

```bash
python code/realtime_gui.py --record 01 --window 10 --step 0.25
```

论文中建议写法：

> 在常规离线分析之外，本文进一步设计了一个基于 Tkinter 和 Matplotlib 的实时回放界面，可动态显示 ECG、PPG 和 RESP 三路信号，有助于观察多模态生理信号在时间维度上的同步变化。

## 3. 高质量科研风格图表

已实现。图表统一使用较高分辨率导出，包含标题、坐标轴标签、单位和图例，并覆盖波形、频谱、时频、统计比较、相关性分析和一致性分析等类型。

已生成图表类型：

- 原始信号波形图。
- 滤波后信号波形图。
- 标准化多模态叠加图。
- ECG R 峰检测图。
- PPG 脉搏峰检测图。
- RESP 呼吸峰检测图。
- FFT 频谱图。
- STFT 时频图。
- 跨记录生命体征对比图。
- Bland-Altman 一致性分析图。
- 心肺耦合散点图。
- 多模态融合特征热图。

论文中建议写法：

> 所有图表均使用 Matplotlib 以 300 dpi 分辨率导出，并统一设置标题、坐标轴标签、单位和图例，以提高结果展示的规范性和可读性。

## 4. 创新性分析方法

已实现。相较于只做单一信号滤波和频谱分析，本项目增加了以下扩展分析：

- ECG-PPG 一致性分析：通过 Bland-Altman 图评估 ECG 心率与 PPG 脉率的一致程度。
- ECG-PPG 峰值时延分析：估计心电活动与外周脉搏波之间的时间关系。
- 心肺耦合分析：分析呼吸率与心率之间的相关关系。
- 多模态融合特征图：将多个跨模态指标归一化后进行可视化比较。

论文中建议写法：

> 在常规时域、频域和时频分析基础上，本文引入 ECG-PPG 一致性分析、峰值时延估计和心肺耦合分析，增强了多模态结果解释的完整性。

## 暂不建议实现的加分项

### 深度学习分析

暂不建议作为本课程论文的主线。原因是：

- 当前任务核心是信号预处理、特征提取和结果解释。
- 数据量只选取 3 条记录，不适合训练可靠深度学习模型。
- 如果强行加入深度学习，容易出现模型泛化不足、训练过程解释不清和论文重点偏移的问题。

如果确实想体现一点机器学习，可以后续加入简单的 PCA、K-means 或逻辑回归作为补充，但不建议为了加分强行训练神经网络。

### GitHub 项目管理

可选。当前代码结构已经比较清晰，如果后续上传到 GitHub 或 Gitee，可以再补充：

- `README.md`
- `requirements.txt`
- `code/`
- `figures/`
- `results/`
- 规范提交记录

论文附录中可说明“项目代码已按模块化结构组织”，但如果没有真实远程仓库链接，不建议虚写 GitHub 项目管理。
