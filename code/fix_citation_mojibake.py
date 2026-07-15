from pathlib import Path

from docx import Document


BASE_DIR = Path(__file__).resolve().parents[1]
src = BASE_DIR / "docs" / "course_paper_format_checked_cited.docx"
out = BASE_DIR / "docs" / "course_paper_format_checked_cited_fixed.docx"

doc = Document(str(src))

replacements = {
    19: (
        "生物医学信号处理是生物医学工程专业的重要基础内容，其目标是从复杂、含噪的生理信号中提取具有医学意义的信息。"
        "在临床监护、可穿戴健康设备和远程医疗场景中，心电、光电容积脉搏波和呼吸信号是最常见的生命体征信号。"
        "ECG 直接反映心脏电活动，能够较准确地定位心搏事件；PPG 通过光学方式反映外周组织血容量变化，常用于脉率和血氧相关监测；"
        "呼吸信号则反映通气节律，是评估患者基础生理状态的重要指标。三类信号从不同生理机制出发描述人体状态，具有天然互补性。"
        "PhysioNet 为复杂生理信号公开共享和可复现研究提供了重要平台[2]；PPG 信号处理与脉搏波形分析也已有较成熟的方法基础[4]。"
    ),
    23: (
        "本文使用的数据集为 PhysioNet 平台发布的 BIDMC PPG and Respiration Dataset v1.0.0。"
        "该数据集来源于 Beth Israel Deaconess Medical Center 的危重患者监护记录，包含 ECG、PPG/PLETH、阻抗呼吸信号、生命体征数值以及呼吸相关标注。"
        "数据集总共包含 53 条记录，每条记录约 8 min，波形信号采样率为 125 Hz。"
        "由于课程论文更强调完整处理流程和独立分析，本文选取 bidmc_01、bidmc_02 和 bidmc_03 三条记录作为代表性样本，每条记录按 30 s 窗口切分，共得到 60 个分析窗口。"
        "上述数据集说明与记录结构以 PhysioNet 官方数据集页面为依据[7]；该数据也曾用于从脉搏血氧波形估计呼吸率的相关研究[1]。"
    ),
    37: (
        "本文至少使用三类分析方法。第一类为时域分析，主要通过峰值检测定位 ECG R 峰、PPG 脉搏峰和呼吸峰，并由相邻峰间期计算心率、脉率和呼吸率。"
        "ECG R 峰检测设置最小峰距约 0.35 s，以避免同一次心搏被重复识别；PPG 峰值检测设置最小峰距约 0.40 s；"
        "呼吸峰值检测设置更长的最小峰距，以适应较低的呼吸频率。在 ECG 特征中，本文进一步计算 SDNN 和 RMSSD。"
        "SDNN 反映 RR 间期总体波动，RMSSD 反映相邻 RR 间期短期变化，是常用 HRV 指标。"
        "HRV 指标定义和解释参考了心率变异性测量标准中的经典表述[3]。"
    ),
    38: (
        "第二类为频域分析。本文对滤波后信号进行快速傅里叶变换，计算归一化频谱，并在相应频率范围内寻找主频率。"
        "ECG 和 PPG 的主频率与心率或脉率相关，呼吸信号的主频率则对应呼吸节律。"
        "频域分析能够验证峰值检测得到的生命体征估计是否落在合理范围内。"
        "滤波、峰值检测和频谱分析等步骤主要基于 SciPy 信号处理模块实现[5]。"
    ),
    79: (
        "除离线分析外，本文设计了一个实时可视化界面，用于回放处理后的 ECG、PPG 和 RESP 三路信号。"
        "界面基于 Python 标准库 Tkinter 和 Matplotlib 实现，不需要额外复杂框架。"
        "用户可以选择记录编号，设置信号显示窗口长度和播放步长，通过播放、暂停、重置和滑动条查看不同时间段的多模态信号。"
        "界面中的波形绘制和图表导出主要使用 Matplotlib 完成[6]。"
    ),
}

for idx, text in replacements.items():
    doc.paragraphs[idx].text = text

doc.save(str(out))
print(out)
