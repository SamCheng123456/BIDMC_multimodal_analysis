# GUI 设计说明

本项目新增实时可视化界面，用于展示 ECG、PPG 与 RESP 三路信号的同步变化。

## 运行方式

```bash
python code/realtime_gui.py --record 01
```

可选参数：

```bash
python code/realtime_gui.py --record 01 --window 10 --step 0.25
```

## 界面特点

- 顶部深蓝状态栏显示项目名称、记录编号和当前时间窗口。
- 指标卡片展示 ECG、PPG、RESP 动态范围和采样率。
- 三个同步波形区分别显示 ECG、PPG、RESP 标准化信号。
- 底部提供播放、重置和时间轴滑动控制。
- 视觉风格与生物医学监护、生命体征看板场景相匹配。

## 论文展示图

生成 GUI 展示图：

```bash
python code/generate_gui_preview.py --record 01 --start 40 --window 10
```

输出文件：

```text
figures/gui/fig18_gui_preview.png
```
