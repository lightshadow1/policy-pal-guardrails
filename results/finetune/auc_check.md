# AUC check: ranking quality of the fine-tune, week 2 (threshold-free)

AUC = chance a random positive outscores a random negative (0.5 = chance, 1.0 = perfect). Week 2 only, 1,055 questions. Script: `finetune/auc_check.py`.

## Not-allowed detection (score = highest of the six topic scores)

| model | AUC vs all others (95% CI) | AUC vs in-scope only | TPR at 5% FPR | median score: not-allowed / others | not-allowed above 0.5 |
|---|---|---|---|---|---|
| gliner zero-shot | 0.513 (0.474–0.557) | 0.409 | 11.0% | 0.76 / 0.76 | 93.9% |
| ft seed 42 | 0.740 (0.709–0.769) | 0.966 | 18.9% | 2.4e-06 / 1.3e-06 | 0.0% |
| ft seed 43 | 0.715 (0.676–0.746) | 0.969 | 26.5% | 1.7e-05 / 1.1e-05 | 0.0% |
| ft seed 44 | 0.450 (0.408–0.494) | 0.437 | 7.2% | 2e-05 / 2.2e-05 | 0.0% |
| jev round 2 (ref) | 0.906 (0.884–0.929) | 0.898 | 70.8% | 0.85 / 0.06 | 71.6% |

## Per topic (AUC of that topic's score; positives = that topic, negatives = every question that is not 'not allowed')

| model | legal | medical | investment | prompt_attack | privacy | harmful |
|---|---|---|---|---|---|---|
| gliner zero-shot | 0.797 | 0.956 | 0.856 | 0.865 | 0.907 | 0.931 |
| ft seed 42 | 0.585 | 0.839 | 0.837 | 0.928 | 0.939 | 0.823 |
| ft seed 43 | 0.589 | 0.676 | 0.797 | 0.789 | 0.930 | 0.925 |
| ft seed 44 | 0.513 | 0.736 | 0.632 | 0.808 | 0.579 | 0.548 |
| jev round 2 (ref) | 0.978 | 0.992 | 0.983 | 0.973 | 0.956 | 0.958 |

## The other two decisions

| model | in scope vs irrelevant (AUC) | ambiguous vs rest (AUC) |
|---|---|---|
| gliner zero-shot | 0.773 | 0.455 |
| ft seed 42 | 0.986 | 0.461 |
| ft seed 43 | 0.986 | 0.602 |
| ft seed 44 | 0.990 | 0.738 |
| jev round 2 (ref) | 0.980 | 0.715 |
