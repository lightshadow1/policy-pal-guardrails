# GLiNER fine-tune vs base and Jev (week 2)

Week 2: 1055 questions. Thresholds either 0.5 (no labelled data) or tuned on the held-out dev set: 156 week 1 questions, only 8 of them ambiguous, so the tuned thresholds are noisy. Accuracy alone misleads here: a model that never refuses still scores high on week 2's mix, so read macro-F1 and the not-allowed column.

| model | thresholds | accuracy (95% CI) | macro-F1 | in-scope answered | in-scope refused | irrelevant | not allowed | ambiguous |
|---|---|---|---|---|---|---|---|---|
| gliner-base | 0.5 | 24.3% (21.7%–26.8%) | 12.6% | 0.0% | 99.6% | 0.6% | 93.9% | 9.3% |
| gliner-base | dev-tuned | 19.1% (16.9%–21.6%) | 15.8% | 0.0% | 15.4% | 0.2% | 59.5% | 81.5% |
| gliner-ft_s42 | 0.5 | 66.6% (63.8%–69.4%) | 40.9% | 93.6% | 6.4% | 96.2% | 0.0% | 0.0% |
| gliner-ft_s42 | dev-tuned | 54.8% (51.8%–57.7%) | 45.2% | 91.0% | 9.0% | 25.0% | 90.5% | 0.0% |
| gliner-ft_s43 | 0.5 | 65.8% (62.8%–68.6%) | 41.1% | 93.6% | 6.4% | 94.2% | 0.0% | 1.9% |
| gliner-ft_s43 | dev-tuned | 49.4% (46.4%–52.3%) | 48.5% | 92.7% | 7.3% | 18.5% | 75.8% | 20.4% |
| gliner-ft_s44 | 0.5 | 66.7% (63.8%–69.6%) | 41.0% | 94.9% | 5.1% | 95.8% | 0.0% | 0.0% |
| gliner-ft_s44 | dev-tuned | 34.2% (31.4%–37.0%) | 29.1% | 39.3% | 60.3% | 1.8% | 96.6% | 9.3% |
| jev-r2 | 0.5 | 53.3% (50.3%–56.1%) | 49.4% | 24.8% | 5.1% | 53.7% | 72.0% | 81.5% |
| jev-r2 | dev-tuned | 62.7% (60.0%–65.6%) | 56.0% | 49.6% | 8.1% | 66.8% | 70.5% | 44.4% |
| gliner-zeroshot (served schema) | 0.5 | 24.3% (21.7%–26.8%) | 12.6% | 0.0% | 99.6% | 0.6% | 93.9% | 9.3% |
| gliner-zeroshot (served schema) | dev-tuned | 19.1% (16.9%–21.6%) | 15.8% | 0.0% | 15.4% | 0.2% | 59.5% | 81.5% |

Fine-tune, 0.5: macro-F1 mean 41.0% (range 40.9%–41.1%) over 3 seeds.

Fine-tune, dev-tuned: macro-F1 mean 40.9% (range 29.1%–48.5%) over 3 seeds.
