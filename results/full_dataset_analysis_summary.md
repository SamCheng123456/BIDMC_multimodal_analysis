# Full-Dataset BIDMC Analysis Summary

## Processing Scope

- Dataset: BIDMC PPG and Respiration Dataset v1.0.0.
- Records processed: 53 / 53.
- Signal files used: `bidmc_01_Signals.csv` to `bidmc_53_Signals.csv`.
- Monitor reference files used: `bidmc_01_Numerics.csv` to `bidmc_53_Numerics.csv`.
- Windowing strategy: 30 s non-overlapping windows.
- Total analysis windows: 848.
- Sampling rate handling: estimated as `(n_samples - 1) / duration`, giving 125 Hz for BIDMC CSV signals. This avoids the rounding problem in the three-decimal `Time [s]` column.

## Signal-Derived Feature Summary

| Feature | Mean | Std | Median | Min | Max |
|---|---:|---:|---:|---:|---:|
| ECG heart rate (bpm) | 95.243 | 14.879 | 91.377 | 57.096 | 148.754 |
| PPG pulse rate (bpm) | 88.386 | 12.673 | 87.887 | 57.447 | 126.119 |
| Respiratory rate (breaths/min) | 18.520 | 3.182 | 18.399 | 8.647 | 33.235 |
| ECG SDNN (ms) | 62.702 | 61.035 | 38.962 | 2.988 | 284.771 |
| ECG RMSSD (ms) | 78.383 | 82.128 | 44.659 | 3.912 | 410.869 |
| ECG-PPG absolute rate error (bpm) | 6.931 | 13.784 | 0.755 | 0.000 | 67.018 |

## Monitor Numerics Comparison

The official BIDMC `Numerics.csv` files were used as a reference for HR, PULSE and RESP values. At record level, 40 records passed the current quality-control threshold, while 13 records were marked for review because at least one modality had a large discrepancy from the monitor numerics.

| Comparison | Record-level mean MAE | Record-level median MAE | Max record-level MAE |
|---|---:|---:|---:|
| ECG HR vs monitor HR (bpm) | 6.348 | 0.658 | 66.637 |
| PPG PR vs monitor PULSE (bpm) | 1.953 | 1.014 | 15.351 |
| RESP RR vs monitor RESP (breaths/min) | 1.595 | 0.742 | 10.755 |

Window-level median absolute errors were 0.659 bpm for ECG HR, 0.653 bpm for PPG pulse rate and 0.511 breaths/min for respiration rate. This indicates that most windows are consistent with monitor numerics, while a smaller set of records should be discussed as signal-quality or peak-detection edge cases.

## Records Marked For Review

The following records had at least one modality exceeding the current review threshold:

`04, 13, 17, 19, 23, 31, 33, 35, 40, 41, 44, 47, 53`.

The largest discrepancies were mainly caused by ECG peak over-detection in several records, where the signal-derived ECG heart rate was approximately twice the monitor HR. These cases should not be hidden; they are useful evidence for discussing the necessity of signal quality control in full-dataset analysis.

## Generated Full-Dataset Figures

- `fig19_full_dataset_vital_sign_distributions.png`
- `fig20_ranked_hr_pr_error_all_records.png`
- `fig21_full_dataset_feature_correlation.png`
- `fig22_full_dataset_record_feature_map.png`
- `fig23_signal_vs_monitor_error_distribution.png`
- `fig24_signal_monitor_agreement_scatter.png`
- `fig25_record_quality_flags.png`
