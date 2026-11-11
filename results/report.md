# Round 1 vs round 2 (and 2b: in scope checked before ambiguous)

Week 2 (test) only: 1055 questions. Week 1 (1036) is used for the review and for tuning; its numbers are in the last section.

## Headline

| guardrail | accuracy (95% CI) | macro-F1 | false refusals: all / covered / not covered | pairs both right | cost per 1k | p50 / p95 |
|---|---|---|---|---|---|---|
| regex | 26.5% (23.9%–29.2%) | 14.9% | 1.3% / 1.4% / 1.2% | 0.0% | $0.0000 | 0 / 1 ms |
| jev-r1 | 33.1% (30.1%–35.8%) | 24.8% | 4.3% / 5.4% / 3.8% | 46.7% | $0.0186 | 94 / 159 ms |
| gliner-r1 | 21.6% (19.1%–24.1%) | 9.7% | 99.6% / 98.6% / 100.0% | 0.0% | $0.0000 | 70 / 120 ms |
| jev-r2@0.5 | 53.3% (50.3%–56.1%) | 49.4% | 5.1% / 6.8% / 4.4% | 30.0% | $0.0257 | 94 / 159 ms |
| jev-r2-tuned | 61.3% (58.4%–64.1%) | 55.3% | 6.4% / 5.4% / 6.9% | 63.3% | $0.0257 | 94 / 159 ms |
| jev-r2b@0.5 | 66.4% (63.6%–69.3%) | 63.1% | 5.1% / 6.8% / 4.4% | 86.7% | $0.0257 | 94 / 159 ms |
| jev-r2b-tuned | 70.3% (67.4%–73.0%) | 63.6% | 6.4% / 5.4% / 6.9% | 96.7% | $0.0257 | 94 / 159 ms |
| gliner-r2@0.5 | 24.3% (21.7%–26.8%) | 12.6% | 99.6% / 100.0% / 99.4% | 0.0% | $0.0000 | 80 / 134 ms |
| gliner-r2-tuned | 48.1% (44.9%–51.1%) | 40.1% | 42.3% / 35.1% / 45.6% | 50.0% | $0.0000 | 80 / 134 ms |
| gliner-r2b@0.5 | 24.3% (21.7%–26.8%) | 12.6% | 99.6% / 100.0% / 99.4% | 0.0% | $0.0000 | 80 / 134 ms |
| gliner-r2b-tuned | 48.0% (44.8%–50.9%) | 39.6% | 42.3% / 35.1% / 45.6% | 50.0% | $0.0000 | 80 / 134 ms |

False refusal = an in-scope question labelled not allowed or irrelevant. Asking for detail isn't counted as a refusal.

## Recall per label

| guardrail | in_scope | irrelevant | not_allowed | ambiguous |
|---|---|---|---|---|
| regex | 98.7% | 7.4% | 4.5% | 0.0% |
| jev-r1 | 95.7% | 7.4% | 33.3% | 0.0% |
| gliner-r1 | 0.4% | 0.8% | 84.5% | 0.0% |
| jev-r2@0.5 | 24.8% | 53.7% | 72.0% | 81.5% |
| jev-r2-tuned | 46.6% | 65.4% | 69.7% | 46.3% |
| jev-r2b@0.5 | 86.3% | 53.7% | 72.0% | 72.2% |
| jev-r2b-tuned | 88.0% | 65.4% | 69.7% | 42.6% |
| gliner-r2@0.5 | 0.0% | 0.6% | 93.9% | 9.3% |
| gliner-r2-tuned | 57.3% | 34.4% | 73.9% | 9.3% |
| gliner-r2b@0.5 | 0.0% | 0.6% | 93.9% | 9.3% |
| gliner-r2b-tuned | 57.3% | 34.4% | 73.9% | 7.4% |

## Not allowed: caught (any topic) / right topic

| guardrail | legal | medical | investment | privacy | harmful | prompt_attack |
|---|---|---|---|---|---|---|
| regex | 0.0% / 0.0% | 0.0% / 0.0% | 2.6% / 2.6% | 0.0% / 0.0% | 4.4% / 0.0% | 20.6% / 20.6% |
| jev-r1 | 63.0% / 63.0% | 75.0% / 75.0% | 76.9% / 76.9% | 0.0% / 0.0% | 8.9% / 0.0% | 52.9% / 52.9% |
| gliner-r1 | 100.0% / 81.5% | 90.0% / 75.0% | 100.0% / 100.0% | 64.8% / 0.0% | 86.7% / 0.0% | 76.5% / 35.3% |
| jev-r2@0.5 | 66.7% / 66.7% | 70.0% / 70.0% | 76.9% / 76.9% | 94.4% / 79.6% | 65.6% / 58.9% | 52.9% / 52.9% |
| jev-r2-tuned | 59.3% / 59.3% | 50.0% / 50.0% | 56.4% / 56.4% | 94.4% / 79.6% | 73.3% / 66.7% | 55.9% / 55.9% |
| jev-r2b@0.5 | 66.7% / 66.7% | 70.0% / 70.0% | 76.9% / 76.9% | 94.4% / 79.6% | 65.6% / 58.9% | 52.9% / 52.9% |
| jev-r2b-tuned | 59.3% / 59.3% | 50.0% / 50.0% | 56.4% / 56.4% | 94.4% / 79.6% | 73.3% / 66.7% | 55.9% / 55.9% |
| gliner-r2@0.5 | 96.3% / 33.3% | 95.0% / 50.0% | 100.0% / 100.0% | 96.3% / 66.7% | 96.7% / 83.3% | 73.5% / 8.8% |
| gliner-r2-tuned | 48.1% / 29.6% | 90.0% / 90.0% | 51.3% / 51.3% | 87.0% / 70.4% | 83.3% / 78.9% | 64.7% / 44.1% |
| gliner-r2b@0.5 | 96.3% / 33.3% | 95.0% / 50.0% | 100.0% / 100.0% | 96.3% / 66.7% | 96.7% / 83.3% | 73.5% / 8.8% |
| gliner-r2b-tuned | 48.1% / 29.6% | 90.0% / 90.0% | 51.3% / 51.3% | 87.0% / 70.4% | 83.3% / 78.9% | 64.7% / 44.1% |

## Accuracy per source

| source | n | regex | jev-r1 | gliner-r1 | jev-r2@0.5 | jev-r2-tuned | jev-r2b@0.5 | jev-r2b-tuned | gliner-r2@0.5 | gliner-r2-tuned | gliner-r2b@0.5 | gliner-r2b-tuned |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| aegis | 175 | 6.3% | 8.6% | 48.6% | 50.9% | 56.0% | 50.9% | 56.0% | 54.3% | 61.1% | 54.3% | 61.1% |
| clinc | 397 | 42.6% | 45.1% | 4.3% | 39.0% | 54.9% | 65.5% | 73.0% | 4.5% | 49.6% | 4.5% | 49.6% |
| coconot | 40 | 0.0% | 0.0% | 62.5% | 97.5% | 97.5% | 97.5% | 97.5% | 97.5% | 90.0% | 97.5% | 90.0% |
| deepset | 31 | 12.9% | 45.2% | 71.0% | 48.4% | 51.6% | 48.4% | 51.6% | 67.7% | 61.3% | 67.7% | 61.3% |
| pairs | 60 | 50.0% | 73.3% | 33.3% | 65.0% | 81.7% | 93.3% | 98.3% | 35.0% | 71.7% | 35.0% | 71.7% |
| policypal | 42 | 90.5% | 88.1% | 9.5% | 35.7% | 52.4% | 85.7% | 88.1% | 7.1% | 69.0% | 7.1% | 66.7% |
| se:askubuntu | 15 | 0.0% | 0.0% | 0.0% | 73.3% | 73.3% | 73.3% | 73.3% | 0.0% | 46.7% | 0.0% | 46.7% |
| se:health | 51 | 0.0% | 21.6% | 25.5% | 62.7% | 58.8% | 62.7% | 58.8% | 29.4% | 29.4% | 29.4% | 29.4% |
| se:law | 51 | 0.0% | 19.6% | 39.2% | 60.8% | 62.7% | 60.8% | 62.7% | 37.3% | 23.5% | 37.3% | 23.5% |
| se:money | 51 | 2.0% | 21.6% | 37.3% | 66.7% | 54.9% | 66.7% | 54.9% | 37.3% | 19.6% | 37.3% | 19.6% |
| se:superuser | 15 | 6.7% | 6.7% | 0.0% | 80.0% | 86.7% | 80.0% | 86.7% | 0.0% | 60.0% | 0.0% | 60.0% |
| se:workplace | 51 | 9.8% | 11.8% | 2.0% | 60.8% | 54.9% | 52.9% | 51.0% | 9.8% | 17.6% | 9.8% | 17.6% |
| xstest | 76 | 27.6% | 27.6% | 2.6% | 77.6% | 82.9% | 77.6% | 82.9% | 1.3% | 18.4% | 1.3% | 18.4% |

## Paired comparison (McNemar, Holm-adjusted)

| A | B | only A right | only B right | p (Holm) |
|---|---|---|---|---|
| regex | jev-r1 | 10 | 79 | 3.75e-13 |
| regex | gliner-r1 | 267 | 215 | 0.1 |
| regex | jev-r2@0.5 | 188 | 470 | 2.38e-27 |
| regex | jev-r2-tuned | 135 | 502 | 5.58e-49 |
| regex | jev-r2b@0.5 | 47 | 468 | 1.31e-86 |
| regex | jev-r2b-tuned | 41 | 503 | 1.91e-100 |
| regex | gliner-r2@0.5 | 270 | 246 | 1 |
| regex | gliner-r2-tuned | 129 | 356 | 3.22e-24 |
| regex | gliner-r2b@0.5 | 270 | 246 | 1 |
| regex | gliner-r2b-tuned | 129 | 355 | 4.54e-24 |
| jev-r1 | gliner-r1 | 259 | 138 | 1.8e-08 |
| jev-r1 | jev-r2@0.5 | 180 | 393 | 6.73e-18 |
| jev-r1 | jev-r2-tuned | 144 | 442 | 1.12e-34 |
| jev-r1 | jev-r2b@0.5 | 40 | 392 | 4.51e-72 |
| jev-r1 | jev-r2b-tuned | 51 | 444 | 1.23e-77 |
| jev-r1 | gliner-r2@0.5 | 266 | 173 | 0.000137 |
| jev-r1 | gliner-r2-tuned | 146 | 304 | 1.43e-12 |
| jev-r1 | gliner-r2b@0.5 | 266 | 173 | 0.000137 |
| jev-r1 | gliner-r2b-tuned | 146 | 303 | 1.84e-12 |
| gliner-r1 | jev-r2@0.5 | 62 | 396 | 5.28e-59 |
| gliner-r1 | jev-r2-tuned | 71 | 490 | 2.46e-76 |
| gliner-r1 | jev-r2b@0.5 | 62 | 535 | 3.55e-93 |
| gliner-r1 | jev-r2b-tuned | 71 | 585 | 9.48e-100 |
| gliner-r1 | gliner-r2@0.5 | 15 | 43 | 0.00276 |
| gliner-r1 | gliner-r2-tuned | 59 | 338 | 4.68e-47 |
| gliner-r1 | gliner-r2b@0.5 | 15 | 43 | 0.00276 |
| gliner-r1 | gliner-r2b-tuned | 59 | 337 | 7.76e-47 |
| jev-r2@0.5 | jev-r2-tuned | 40 | 125 | 3.74e-10 |
| jev-r2@0.5 | jev-r2b@0.5 | 5 | 144 | 5.31e-35 |
| jev-r2@0.5 | jev-r2b-tuned | 42 | 222 | 2.88e-29 |
| jev-r2@0.5 | gliner-r2@0.5 | 375 | 69 | 2.28e-50 |
| jev-r2@0.5 | gliner-r2-tuned | 258 | 203 | 0.073 |
| jev-r2@0.5 | gliner-r2b@0.5 | 375 | 69 | 2.28e-50 |
| jev-r2@0.5 | gliner-r2b-tuned | 259 | 203 | 0.073 |
| jev-r2-tuned | jev-r2b@0.5 | 78 | 132 | 0.00237 |
| jev-r2-tuned | jev-r2b-tuned | 2 | 97 | 4.06e-25 |
| jev-r2-tuned | gliner-r2@0.5 | 467 | 76 | 5.47e-68 |
| jev-r2-tuned | gliner-r2-tuned | 294 | 154 | 5.37e-10 |
| jev-r2-tuned | gliner-r2b@0.5 | 467 | 76 | 5.47e-68 |
| jev-r2-tuned | gliner-r2b-tuned | 295 | 154 | 4.34e-10 |
| jev-r2b@0.5 | jev-r2b-tuned | 38 | 79 | 0.00208 |
| jev-r2b@0.5 | gliner-r2@0.5 | 514 | 69 | 2.14e-83 |
| jev-r2b@0.5 | gliner-r2-tuned | 318 | 124 | 2.22e-19 |
| jev-r2b@0.5 | gliner-r2b@0.5 | 514 | 69 | 2.14e-83 |
| jev-r2b@0.5 | gliner-r2b-tuned | 319 | 124 | 1.61e-19 |
| jev-r2b-tuned | gliner-r2@0.5 | 562 | 76 | 7.8e-91 |
| jev-r2b-tuned | gliner-r2-tuned | 338 | 103 | 8.01e-29 |
| jev-r2b-tuned | gliner-r2b@0.5 | 562 | 76 | 7.8e-91 |
| jev-r2b-tuned | gliner-r2b-tuned | 339 | 103 | 5.4e-29 |
| gliner-r2@0.5 | gliner-r2-tuned | 65 | 316 | 3.89e-39 |
| gliner-r2@0.5 | gliner-r2b@0.5 | 0 | 0 | 1 |
| gliner-r2@0.5 | gliner-r2b-tuned | 65 | 315 | 6.11e-39 |
| gliner-r2-tuned | gliner-r2b@0.5 | 316 | 65 | 3.89e-39 |
| gliner-r2-tuned | gliner-r2b-tuned | 1 | 0 | 1 |
| gliner-r2b@0.5 | gliner-r2b-tuned | 65 | 315 | 6.11e-39 |

## Confusion matrices (rows = true label, columns = predicted)

**regex**

| | in_scope | irrelevant | not_allowed | ambiguous |
|---|---|---|---|---|
| in_scope | 231 | 3 | 0 | 0 |
| irrelevant | 463 | 37 | 3 | 0 |
| not_allowed | 240 | 12 | 12 | 0 |
| ambiguous | 51 | 3 | 0 | 0 |

**jev-r1**

| | in_scope | irrelevant | not_allowed | ambiguous |
|---|---|---|---|---|
| in_scope | 224 | 3 | 7 | 0 |
| irrelevant | 440 | 37 | 26 | 0 |
| not_allowed | 170 | 6 | 88 | 0 |
| ambiguous | 51 | 3 | 0 | 0 |

**gliner-r1**

| | in_scope | irrelevant | not_allowed | ambiguous |
|---|---|---|---|---|
| in_scope | 1 | 0 | 233 | 0 |
| irrelevant | 46 | 4 | 453 | 0 |
| not_allowed | 41 | 0 | 223 | 0 |
| ambiguous | 5 | 0 | 49 | 0 |

**jev-r2@0.5**

| | in_scope | irrelevant | not_allowed | ambiguous |
|---|---|---|---|---|
| in_scope | 58 | 5 | 7 | 164 |
| irrelevant | 4 | 270 | 43 | 186 |
| not_allowed | 2 | 38 | 190 | 34 |
| ambiguous | 7 | 3 | 0 | 44 |

**jev-r2-tuned**

| | in_scope | irrelevant | not_allowed | ambiguous |
|---|---|---|---|---|
| in_scope | 109 | 12 | 3 | 110 |
| irrelevant | 6 | 329 | 43 | 125 |
| not_allowed | 2 | 55 | 184 | 23 |
| ambiguous | 10 | 19 | 0 | 25 |

**jev-r2b@0.5**

| | in_scope | irrelevant | not_allowed | ambiguous |
|---|---|---|---|---|
| in_scope | 202 | 5 | 7 | 20 |
| irrelevant | 15 | 270 | 43 | 175 |
| not_allowed | 3 | 38 | 190 | 33 |
| ambiguous | 12 | 3 | 0 | 39 |

**jev-r2b-tuned**

| | in_scope | irrelevant | not_allowed | ambiguous |
|---|---|---|---|---|
| in_scope | 206 | 12 | 3 | 13 |
| irrelevant | 14 | 329 | 43 | 117 |
| not_allowed | 2 | 55 | 184 | 23 |
| ambiguous | 12 | 19 | 0 | 23 |

**gliner-r2@0.5**

| | in_scope | irrelevant | not_allowed | ambiguous |
|---|---|---|---|---|
| in_scope | 0 | 0 | 233 | 1 |
| irrelevant | 1 | 3 | 473 | 26 |
| not_allowed | 0 | 2 | 248 | 14 |
| ambiguous | 0 | 0 | 49 | 5 |

**gliner-r2-tuned**

| | in_scope | irrelevant | not_allowed | ambiguous |
|---|---|---|---|---|
| in_scope | 134 | 24 | 75 | 1 |
| irrelevant | 117 | 173 | 192 | 21 |
| not_allowed | 33 | 29 | 195 | 7 |
| ambiguous | 19 | 16 | 14 | 5 |

**gliner-r2b@0.5**

| | in_scope | irrelevant | not_allowed | ambiguous |
|---|---|---|---|---|
| in_scope | 0 | 0 | 233 | 1 |
| irrelevant | 1 | 3 | 473 | 26 |
| not_allowed | 0 | 2 | 248 | 14 |
| ambiguous | 0 | 0 | 49 | 5 |

**gliner-r2b-tuned**

| | in_scope | irrelevant | not_allowed | ambiguous |
|---|---|---|---|---|
| in_scope | 134 | 24 | 75 | 1 |
| irrelevant | 123 | 173 | 192 | 15 |
| not_allowed | 34 | 29 | 195 | 6 |
| ambiguous | 20 | 16 | 14 | 4 |

## Week 1 (review and tuning set)

| guardrail | accuracy | macro-F1 | false refusals |
|---|---|---|---|
| regex | 26.4% | 15.1% | 0.9% |
| jev-r1 | 33.5% | 24.9% | 3.0% |
| gliner-r1 | 23.3% | 10.6% | 98.3% |
| jev-r2@0.5 | 56.7% | 52.4% | 4.3% |
| jev-r2-tuned | 68.2% | 61.4% | 4.8% |
| jev-r2b@0.5 | 68.6% | 64.6% | 4.3% |
| jev-r2b-tuned | 75.9% | 69.0% | 4.8% |
| gliner-r2@0.5 | 24.3% | 11.1% | 98.7% |
| gliner-r2-tuned | 50.3% | 41.7% | 44.3% |
| gliner-r2b@0.5 | 24.3% | 11.1% | 98.7% |
| gliner-r2b-tuned | 50.2% | 40.0% | 44.3% |

## What adding the discovered topics cost

| guardrail | change | labelled data | training |
|---|---|---|---|
| regex (as shipped) | a phrase list per topic (described, not done: the baseline stays unchanged) | no | no |
| Jev | 4 new questions, 92 words | none at 0.5; ~1,000 labelled week 1 questions to tune thresholds | no |
| GLiNER base, zero-shot | 6 new label descriptions, 114 words | none at 0.5; ~1,000 labelled week 1 questions to tune thresholds | no |
| GLiNER fine-tune (measured later: docs/2026-11-04-finetune.md) | new labelled data and a retrain: 1,344 records, about 17 min per seed on a 1080 Ti | yes | yes |
