# GLiNER fine-tune v2 vs base and Jev (week 2)

Week 2: 1055 questions. Thresholds either 0.5 (no labelled data) or tuned on the held-out dev set: 239 week 1 questions, 11 of them ambiguous. Accuracy alone misleads here: a model that never refuses still scores high on week 2's mix, so read macro-F1 and the not-allowed column.

Checkpoint per seed, chosen by dev macro-F1 at 0.5: ft_s42_best (41.9%), ft_s43_final (42.3%), ft_s44_best (41.0%).

| model | thresholds | accuracy (95% CI) | macro-F1 | in-scope answered | in-scope refused | irrelevant | not allowed | ambiguous |
|---|---|---|---|---|---|---|---|---|
| gliner-base | 0.5 | 23.8% (21.2%–26.4%) | 17.4% | 0.0% | 65.4% | 7.6% | 69.3% | 55.6% |
| gliner-base | dev-tuned | 52.6% (49.6%–55.7%) | 43.1% | 45.3% | 54.3% | 53.9% | 65.2% | 11.1% |
| gliner-ft_s42_best | 0.5 | 67.4% (64.5%–70.1%) | 43.0% | 95.3% | 4.7% | 96.6% | 0.0% | 3.7% |
| gliner-ft_s42_best | dev-tuned | 66.7% (63.8%–69.5%) | 50.1% | 96.2% | 3.4% | 91.8% | 0.0% | 31.5% |
| gliner-ft_s43_final | 0.5 | 65.6% (62.7%–68.4%) | 40.0% | 96.6% | 3.4% | 92.6% | 0.0% | 0.0% |
| gliner-ft_s43_final | dev-tuned | 65.7% (62.7%–68.5%) | 40.1% | 96.2% | 3.8% | 93.0% | 0.0% | 0.0% |
| gliner-ft_s44_best | 0.5 | 66.2% (63.3%–68.9%) | 41.1% | 96.2% | 3.8% | 93.8% | 0.0% | 1.9% |
| gliner-ft_s44_best | dev-tuned | 65.9% (63.0%–68.7%) | 40.8% | 96.6% | 3.4% | 93.0% | 0.0% | 1.9% |
| jev-r2 | 0.5 | 53.3% (50.3%–56.1%) | 49.4% | 24.8% | 5.1% | 53.7% | 72.0% | 81.5% |
| jev-r2 | dev-tuned | 75.5% (72.8%–78.0%) | 62.8% | 83.8% | 11.1% | 79.5% | 72.7% | 14.8% |
| gliner-zeroshot (served schema) | 0.5 | 24.3% (21.7%–26.8%) | 12.6% | 0.0% | 99.6% | 0.6% | 93.9% | 9.3% |
| gliner-zeroshot (served schema) | dev-tuned | 51.7% (48.6%–54.9%) | 43.2% | 58.5% | 41.0% | 47.3% | 62.1% | 11.1% |

Fine-tune, 0.5: macro-F1 mean 41.3% (range 40.0%–43.0%) over 3 seeds.

Fine-tune, dev-tuned: macro-F1 mean 43.7% (range 40.1%–50.1%) over 3 seeds.
