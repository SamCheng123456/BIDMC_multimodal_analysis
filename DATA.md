# Data Access

This repository does not include the full BIDMC waveform CSV files to keep the GitHub repository lightweight.

Dataset: BIDMC PPG and Respiration Dataset v1.0.0
Source: https://physionet.org/content/bidmc/1.0.0/

Expected local layout after downloading:

```text
data/raw/bidmc_01_Signals.csv
...
data/raw/bidmc_53_Signals.csv
data/raw/bidmc_01_Numerics.csv
...
data/raw/bidmc_53_Numerics.csv
```

Run the full analysis after placing the data files:

```bash
python code/run_all_records.py
python code/compare_with_numerics.py
```
