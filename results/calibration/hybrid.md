# Hybrid: local scope gate first, Jev only for what it passes (week 2)

Local gate: the v2 fine-tune's scope score (ft_s42_best, ft_s43_final, ft_s44_best). Below the cut, the question is called irrelevant locally and never sent to Jev. Otherwise Jev's round 2 decision stands. The cut quoted per seed is chosen on the v2 dev set (239 week 1 questions) by hybrid macro-F1; the sweep is shown for reference only. Jev's 'week 1 thresholds' were tuned on all of week 1, which includes the dev set.

## Jev at 0.5

| setup | cut | accuracy | macro-F1 | in-scope answered | sent to Jev |
|---|---|---|---|---|---|
| Jev alone | – | 53.3% | 49.4% | 24.8% | 100.0% |
| hybrid, ft_s42_best | 0.1 (dev macro-F1 34.1%) | 53.6% | 31.8% | 23.9% | 26.2% |
| hybrid, ft_s43_final | 0.1 (dev macro-F1 35.8%) | 52.7% | 32.2% | 23.9% | 28.0% |
| hybrid, ft_s44_best | 0.1 (dev macro-F1 38.2%) | 53.7% | 33.1% | 23.1% | 28.2% |

Not-allowed questions (all topics): what happened to them.

| setup | n | caught by Jev | called irrelevant locally (not answered, topic not logged) | **answered** | other (Jev: irrelevant or ambiguous) |
|---|---|---|---|---|---|
| Jev alone | 264 | 190 | 0 | 2 | 72 |
| hybrid, ft_s42_best (cut 0.1) | 264 | 14 | 246 | 2 | 2 |
| hybrid, ft_s43_final (cut 0.1) | 264 | 16 | 245 | 2 | 1 |
| hybrid, ft_s44_best (cut 0.1) | 264 | 25 | 237 | 1 | 1 |

By topic: caught by Jev / local irrelevant / answered (hybrid at the chosen cut).

| setup | harmful | investment | legal | medical | privacy | prompt_attack |
|---|---|---|---|---|---|---|
| Jev alone | 59 / – / 0 | 30 / – / 0 | 18 / – / 2 | 14 / – / 0 | 51 / – / 0 | 18 / – / 0 |
| ft_s42_best | 1 / 89 / 0 | 4 / 35 / 0 | 5 / 19 / 2 | 2 / 17 / 0 | 2 / 52 / 0 | 0 / 34 / 0 |
| ft_s43_final | 0 / 90 / 0 | 4 / 35 / 0 | 6 / 19 / 2 | 2 / 17 / 0 | 3 / 51 / 0 | 1 / 33 / 0 |
| ft_s44_best | 1 / 89 / 0 | 12 / 27 / 0 | 6 / 20 / 1 | 2 / 17 / 0 | 4 / 50 / 0 | 0 / 34 / 0 |

Sweep (week 2, for reference; not used to pick anything): macro-F1 / sent to Jev / not-allowed answered.

| seed | 0.1 | 0.2 | 0.3 | 0.4 | 0.5 | 0.6 | 0.7 | 0.8 | 0.9 |
|---|---|---|---|---|---|---|---|---|---|
| ft_s42_best | 31.8% / 26.2% / 2 | 31.7% / 25.6% / 1 | 31.8% / 25.5% / 1 | 31.4% / 25.1% / 1 | 31.4% / 25.0% / 1 | 31.4% / 25.0% / 1 | 31.2% / 24.8% / 1 | 31.2% / 24.5% / 1 | 30.6% / 23.8% / 0 |
| ft_s43_final | 32.2% / 28.0% / 2 | 32.1% / 27.8% / 1 | 31.9% / 27.7% / 1 | 32.0% / 27.4% / 0 | 31.8% / 27.3% / 0 | 31.8% / 27.2% / 0 | 31.6% / 27.0% / 0 | 31.4% / 26.9% / 0 | 31.3% / 26.6% / 0 |
| ft_s44_best | 33.1% / 28.2% / 1 | 33.1% / 28.0% / 1 | 33.1% / 27.8% / 1 | 33.0% / 27.4% / 1 | 33.0% / 27.3% / 0 | 33.0% / 27.3% / 0 | 33.0% / 27.1% / 0 | 32.9% / 26.9% / 0 | 32.3% / 26.5% / 0 |

## Jev at week 1 thresholds

| setup | cut | accuracy | macro-F1 | in-scope answered | sent to Jev |
|---|---|---|---|---|---|
| Jev alone | – | 61.3% | 55.3% | 46.6% | 100.0% |
| hybrid, ft_s42_best | 0.1 (dev macro-F1 40.6%) | 58.4% | 37.3% | 45.3% | 26.2% |
| hybrid, ft_s43_final | 0.1 (dev macro-F1 42.5%) | 57.8% | 37.7% | 44.9% | 28.0% |
| hybrid, ft_s44_best | 0.1 (dev macro-F1 45.1%) | 58.7% | 38.9% | 44.4% | 28.2% |

Not-allowed questions (all topics): what happened to them.

| setup | n | caught by Jev | called irrelevant locally (not answered, topic not logged) | **answered** | other (Jev: irrelevant or ambiguous) |
|---|---|---|---|---|---|
| Jev alone | 264 | 184 | 0 | 2 | 78 |
| hybrid, ft_s42_best (cut 0.1) | 264 | 14 | 246 | 2 | 2 |
| hybrid, ft_s43_final (cut 0.1) | 264 | 16 | 245 | 2 | 1 |
| hybrid, ft_s44_best (cut 0.1) | 264 | 24 | 237 | 1 | 2 |

By topic: caught by Jev / local irrelevant / answered (hybrid at the chosen cut).

| setup | harmful | investment | legal | medical | privacy | prompt_attack |
|---|---|---|---|---|---|---|
| Jev alone | 66 / – / 0 | 22 / – / 0 | 16 / – / 2 | 10 / – / 0 | 51 / – / 0 | 19 / – / 0 |
| ft_s42_best | 1 / 89 / 0 | 4 / 35 / 0 | 5 / 19 / 2 | 2 / 17 / 0 | 2 / 52 / 0 | 0 / 34 / 0 |
| ft_s43_final | 0 / 90 / 0 | 4 / 35 / 0 | 6 / 19 / 2 | 2 / 17 / 0 | 3 / 51 / 0 | 1 / 33 / 0 |
| ft_s44_best | 1 / 89 / 0 | 11 / 27 / 0 | 6 / 20 / 1 | 2 / 17 / 0 | 4 / 50 / 0 | 0 / 34 / 0 |

Sweep (week 2, for reference; not used to pick anything): macro-F1 / sent to Jev / not-allowed answered.

| seed | 0.1 | 0.2 | 0.3 | 0.4 | 0.5 | 0.6 | 0.7 | 0.8 | 0.9 |
|---|---|---|---|---|---|---|---|---|---|
| ft_s42_best | 37.3% / 26.2% / 2 | 37.3% / 25.6% / 1 | 37.3% / 25.5% / 1 | 36.9% / 25.1% / 1 | 36.9% / 25.0% / 1 | 36.9% / 25.0% / 1 | 36.8% / 24.8% / 1 | 36.8% / 24.5% / 1 | 36.1% / 23.8% / 0 |
| ft_s43_final | 37.7% / 28.0% / 2 | 37.6% / 27.8% / 1 | 37.6% / 27.7% / 1 | 37.7% / 27.4% / 0 | 37.5% / 27.3% / 0 | 37.5% / 27.2% / 0 | 37.2% / 27.0% / 0 | 37.0% / 26.9% / 0 | 36.9% / 26.6% / 0 |
| ft_s44_best | 38.9% / 28.2% / 1 | 38.9% / 28.0% / 1 | 38.9% / 27.8% / 1 | 38.8% / 27.4% / 1 | 38.8% / 27.3% / 0 | 38.8% / 27.3% / 0 | 38.8% / 27.1% / 0 | 38.8% / 26.9% / 0 | 38.1% / 26.5% / 0 |

