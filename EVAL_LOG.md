# Rule Engine Evaluation Log

All evaluations use the unchanged evaluator and 50-plan dataset. Regressed
plans are compared with the immediately preceding kept commit.

| Change | Commit | Precision | Recall | F1 | F0.5 | Claims produced | FP | FN | Regressed plan ids | Result |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | 7fe0adc | 0.738 | 0.614 | 0.670 | 0.709 | 576 | 151 | 122 | 02_filter_projection, 06_long_narrow_pipeline | kept |
| 2 | 78dd0e6 | 0.840 | 0.614 | 0.709 | 0.782 | 506 | 81 | 122 | 02_filter_projection, 06_long_narrow_pipeline | kept |
| 3 | 5245b3e | 0.896 | 0.611 | 0.726 | 0.819 | 479 | 50 | 123 | 06_long_narrow_pipeline | kept |
| 4 | d50dbac | 0.916 | 0.611 | 0.733 | 0.833 | 467 | 39 | 123 | 06_long_narrow_pipeline | kept |
| 5 | dbb4423 | 0.932 | 0.611 | 0.738 | 0.843 | 457 | 31 | 123 | none | kept |
| 6 | f0040cd | 0.928 | 0.617 | 0.741 | 0.843 | 475 | 34 | 121 | none | kept |
| 7 | 44153d4 | 0.926 | 0.649 | 0.763 | 0.853 | 488 | 36 | 111 | none | kept |
| 8 | 40a3071 | 0.928 | 0.649 | 0.764 | 0.854 | 486 | 35 | 111 | none | kept |
