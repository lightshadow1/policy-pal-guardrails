# How many labelled questions does threshold tuning need?

Thresholds tuned on stratified draws from week 1 (1036 questions, label mix {'ambiguous': 49, 'in_scope': 230, 'irrelevant': 495, 'not_allowed': 262}); 200 draws per size, numpy seed 42. Every draw is scored on week 2 (1055 questions). Cells: median, IQR in brackets, 5th–95th percentile in parentheses.

Sanity checks (must reproduce the main report):

- ok   jev r2 full: accuracy 61.3%, macro-F1 55.3% (main report jev-r2-tuned: 61.3%, 55.3%)
- ok   gliner r2 full: accuracy 48.1%, macro-F1 40.1% (main report gliner-r2-tuned: 48.1%, 40.1%)
- ok   jev r2 baseline: accuracy 53.3%, macro-F1 49.4% (main report jev-r2@0.5: 53.3%, 49.4%)
- ok   gliner r2 baseline: accuracy 24.3%, macro-F1 12.6% (main report gliner-r2@0.5: 24.3%, 12.6%)
- ok   jev r2b full: accuracy 70.3%, macro-F1 63.6% (main report jev-r2b-tuned: 70.3%, 63.6%)
- ok   gliner r2b full: accuracy 48.0%, macro-F1 39.6% (main report gliner-r2b-tuned: 48.0%, 39.6%)
- ok   jev r2b baseline: accuracy 66.4%, macro-F1 63.1% (main report jev-r2b@0.5: 66.4%, 63.1%)
- ok   gliner r2b baseline: accuracy 24.3%, macro-F1 12.6% (main report gliner-r2b@0.5: 24.3%, 12.6%)

## Jev, round 2

| tuned on | macro-F1 | beats 0.5 (macro-F1) | accuracy | in-scope answered | in-scope refused | not-allowed caught | ambiguous caught |
|---|---|---|---|---|---|---|---|
| 50 | 54.7% [48.8%–59.3%] (40.0%–62.3%) | 74% | 62.5% (43.8%–75.3%) | 50.4% | 9.2% | 68.2% | 38.9% |
| 100 | 54.9% [52.6%–60.3%] (42.7%–62.5%) | 84% | 61.7% (44.5%–76.4%) | 49.8% | 7.7% | 67.2% | 40.7% |
| 200 | 54.9% [52.8%–60.2%] (45.1%–63.0%) | 90% | 61.1% (48.0%–76.0%) | 47.9% | 7.1% | 71.2% | 44.4% |
| 400 | 54.9% [53.8%–56.1%] (50.5%–63.0%) | 98% | 60.9% (54.3%–75.1%) | 45.3% | 6.4% | 72.0% | 46.3% |
| 800 | 55.0% [54.4%–55.4%] (53.2%–55.9%) | 100% | 61.0% (57.4%–62.2%) | 46.6% | 5.6% | 71.6% | 46.3% |
| all 1,036 | 55.3% | – | 61.3% | 46.6% | 6.4% | 69.7% | 46.3% |
| untuned 0.5 | 49.4% | – | 53.3% | 24.8% | 5.1% | 72.0% | 81.5% |

## Jev, round 2b (in scope before ambiguous; post hoc)

| tuned on | macro-F1 | beats 0.5 (macro-F1) | accuracy | in-scope answered | in-scope refused | not-allowed caught | ambiguous caught |
|---|---|---|---|---|---|---|---|
| 50 | 61.0% [58.3%–62.6%] (53.6%–64.5%) | 18% | 69.4% (56.5%–76.3%) | 85.9% | 9.2% | 68.2% | 38.0% |
| 100 | 62.0% [60.8%–63.1%] (57.5%–64.2%) | 25% | 70.1% (59.1%–77.1%) | 88.5% | 7.7% | 67.2% | 39.8% |
| 200 | 63.1% [61.9%–63.8%] (59.5%–65.0%) | 50% | 70.1% (62.5%–77.0%) | 88.5% | 7.1% | 71.2% | 40.7% |
| 400 | 63.7% [63.0%–64.2%] (62.0%–65.0%) | 73% | 70.2% (66.6%–76.6%) | 88.5% | 6.4% | 72.0% | 42.6% |
| 800 | 63.5% [62.9%–63.9%] (62.4%–64.4%) | 66% | 70.3% (68.7%–71.2%) | 88.9% | 5.6% | 71.6% | 42.6% |
| all 1,036 | 63.6% | – | 70.3% | 88.0% | 6.4% | 69.7% | 42.6% |
| untuned 0.5 | 63.1% | – | 66.4% | 86.3% | 5.1% | 72.0% | 72.2% |

## GLiNER zero-shot, round 2

| tuned on | macro-F1 | beats 0.5 (macro-F1) | accuracy | in-scope answered | in-scope refused | not-allowed caught | ambiguous caught |
|---|---|---|---|---|---|---|---|
| 50 | 25.8% [14.4%–37.1%] (10.7%–41.7%) | 84% | 30.5% (19.5%–50.3%) | 13.5% | 50.2% | 67.0% | 13.0% |
| 100 | 36.1% [25.7%–39.5%] (15.2%–43.8%) | 98% | 42.2% (19.9%–52.2%) | 39.5% | 40.2% | 62.1% | 14.8% |
| 200 | 38.9% [34.7%–40.7%] (16.0%–43.1%) | 99% | 46.0% (19.7%–50.8%) | 50.2% | 41.5% | 64.8% | 14.8% |
| 400 | 39.4% [35.1%–41.0%] (15.7%–42.9%) | 100% | 46.4% (20.7%–50.1%) | 51.7% | 41.9% | 67.4% | 14.8% |
| 800 | 39.4% [37.9%–40.6%] (16.2%–42.0%) | 100% | 46.8% (21.9%–49.4%) | 52.6% | 44.0% | 72.0% | 13.0% |
| all 1,036 | 40.1% | – | 48.1% | 57.3% | 42.3% | 73.9% | 9.3% |
| untuned 0.5 | 12.6% | – | 24.3% | 0.0% | 99.6% | 93.9% | 9.3% |

## GLiNER zero-shot, round 2b (in scope before ambiguous; post hoc)

| tuned on | macro-F1 | beats 0.5 (macro-F1) | accuracy | in-scope answered | in-scope refused | not-allowed caught | ambiguous caught |
|---|---|---|---|---|---|---|---|
| 50 | 29.9% [16.3%–37.1%] (10.6%–41.6%) | 85% | 35.6% (21.7%–50.4%) | 43.6% | 50.2% | 67.0% | 9.3% |
| 100 | 36.7% [31.1%–39.1%] (19.8%–43.6%) | 99% | 43.5% (27.7%–52.1%) | 53.8% | 40.2% | 62.1% | 11.1% |
| 200 | 38.5% [35.3%–40.5%] (26.9%–42.9%) | 99% | 46.4% (30.8%–50.9%) | 55.6% | 41.5% | 64.8% | 11.1% |
| 400 | 39.0% [36.6%–40.6%] (27.8%–42.2%) | 100% | 46.5% (31.7%–50.0%) | 56.0% | 41.9% | 67.4% | 11.1% |
| 800 | 39.0% [37.9%–39.8%] (28.4%–41.6%) | 100% | 46.7% (32.7%–49.4%) | 54.7% | 44.0% | 72.0% | 11.1% |
| all 1,036 | 39.6% | – | 48.0% | 57.3% | 42.3% | 73.9% | 7.4% |
| untuned 0.5 | 12.6% | – | 24.3% | 0.0% | 99.6% | 93.9% | 9.3% |
