# Round 1: day one

Week 2 (test) only: 1055 questions. Week 1 (1036) is used for the review and for tuning; its numbers are in the last section.

## Headline

| guardrail | accuracy (95% CI) | macro-F1 | false refusals: all / covered / not covered | pairs both right | cost per 1k | p50 / p95 |
|---|---|---|---|---|---|---|
| regex | 26.5% (23.9%–29.2%) | 14.9% | 1.3% / 1.4% / 1.2% | 0.0% | $0.0000 | 0 / 1 ms |
| jev-r1 | 33.1% (30.1%–35.8%) | 24.8% | 4.3% / 5.4% / 3.8% | 46.7% | $0.0186 | 94 / 159 ms |
| gliner-r1 | 21.6% (19.1%–24.1%) | 9.7% | 99.6% / 98.6% / 100.0% | 0.0% | $0.0000 | 70 / 120 ms |

False refusal = an in-scope question labelled not allowed or irrelevant. Asking for detail isn't counted as a refusal.

## Recall per label

| guardrail | in_scope | irrelevant | not_allowed | ambiguous |
|---|---|---|---|---|
| regex | 98.7% | 7.4% | 4.5% | 0.0% |
| jev-r1 | 95.7% | 7.4% | 33.3% | 0.0% |
| gliner-r1 | 0.4% | 0.8% | 84.5% | 0.0% |

## Not allowed: caught (any topic) / right topic

| guardrail | legal | medical | investment | privacy | harmful | prompt_attack |
|---|---|---|---|---|---|---|
| regex | 0.0% / 0.0% | 0.0% / 0.0% | 2.6% / 2.6% | 0.0% / 0.0% | 4.4% / 0.0% | 20.6% / 20.6% |
| jev-r1 | 63.0% / 63.0% | 75.0% / 75.0% | 76.9% / 76.9% | 0.0% / 0.0% | 8.9% / 0.0% | 52.9% / 52.9% |
| gliner-r1 | 100.0% / 81.5% | 90.0% / 75.0% | 100.0% / 100.0% | 64.8% / 0.0% | 86.7% / 0.0% | 76.5% / 35.3% |

## Accuracy per source

| source | n | regex | jev-r1 | gliner-r1 |
|---|---|---|---|---|
| aegis | 175 | 6.3% | 8.6% | 48.6% |
| clinc | 397 | 42.6% | 45.1% | 4.3% |
| coconot | 40 | 0.0% | 0.0% | 62.5% |
| deepset | 31 | 12.9% | 45.2% | 71.0% |
| pairs | 60 | 50.0% | 73.3% | 33.3% |
| policypal | 42 | 90.5% | 88.1% | 9.5% |
| se:askubuntu | 15 | 0.0% | 0.0% | 0.0% |
| se:health | 51 | 0.0% | 21.6% | 25.5% |
| se:law | 51 | 0.0% | 19.6% | 39.2% |
| se:money | 51 | 2.0% | 21.6% | 37.3% |
| se:superuser | 15 | 6.7% | 6.7% | 0.0% |
| se:workplace | 51 | 9.8% | 11.8% | 2.0% |
| xstest | 76 | 27.6% | 27.6% | 2.6% |

## Paired comparison (McNemar, Holm-adjusted)

| A | B | only A right | only B right | p (Holm) |
|---|---|---|---|---|
| regex | jev-r1 | 10 | 79 | 5.62e-14 |
| regex | gliner-r1 | 267 | 215 | 0.0201 |
| jev-r1 | gliner-r1 | 259 | 138 | 2.58e-09 |

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

## Week 1 (review and tuning set)

| guardrail | accuracy | macro-F1 | false refusals |
|---|---|---|---|
| regex | 26.4% | 15.1% | 0.9% |
| jev-r1 | 33.5% | 24.9% | 3.0% |
| gliner-r1 | 23.3% | 10.6% | 98.3% |
