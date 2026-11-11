# Threshold calibration and a local scope gate (2026-11-05)

Cached scores only: no API calls and no GPU. Thresholds were only ever tuned on week 1. Week 2 (1,055 questions) was
only scored.

## What was run

1. **Tuner fix** (`ppguard/tune.py`). `tune_thresholds` now keeps the 0.5 default when the fitted scores have
   fewer than two distinct values, as it already did with no positives or no negatives. Before the fix, the v2
   fine-tune's all-zero topic scores got a cut of 0 and refused everything. Regenerating
   `results/finetune_v2/report.md` changes only the three fine-tune dev-tuned rows:
   - before: 25.0% accuracy, 100% refused;
   - after: 65.7–66.7% accuracy, macro-F1 40.1–50.1%, not-allowed 0%, topic thresholds 0.5.
2. **Calibration curve** (`uv run python -m ppguard.calibration curve`). How many labelled questions does
   threshold tuning need?
   - Thresholds are tuned on stratified draws from week 1: sizes 50, 100, 200, 400 and 800, 200 draws each,
     numpy seed 42. Each draw tunes both models, and every draw is scored on week 2.
   - Models: Jev and zero-shot GLiNER, under round 2 rules and round 2b (post hoc).
   - Output: `results/calibration/curve.{md,json,csv,png}`.
3. **Hybrid** (`uv run python -m ppguard.calibration hybrid`). The v2 fine-tune's scope score acts as a local gate:
   below a cut, a question is called irrelevant locally; otherwise Jev's round 2 decision stands.
   - The cut is chosen on the v2 dev set (239 week 1 questions) by hybrid macro-F1.
   - A 0.1–0.9 sweep on week 2 is shown for reference only.
   - Output: `results/calibration/hybrid.{md,json}`.

**Sanity checks (all passed exactly).** The full-pool and untuned points reproduce `results/report_round2.json`:

| | round 2, tuned on all of week 1 | round 2, untuned 0.5 | round 2b, tuned | round 2b, 0.5 |
|---|---|---|---|---|
| Jev: accuracy / macro-F1 | 61.3% / 55.3% | 53.3% / 49.4% | 70.3% / 63.6% | 66.4% / 63.1% |
| GLiNER: accuracy / macro-F1 | 48.1% / 40.1% | 24.3% / 12.6% | 48.0% / 39.6% | 24.3% / 12.6% |

## Calibration curve (week 2 macro-F1: median, with the 5th–95th percentile)

| tuned on | Jev, round 2 | Jev, round 2b | GLiNER, round 2 | GLiNER, round 2b |
|---|---|---|---|---|
| 50 | 54.7% (40.0–62.3%) | 61.0% (53.6–64.5%) | 25.8% (10.7–41.7%) | 29.9% (10.6–41.6%) |
| 100 | 54.9% (42.7–62.5%) | 62.0% (57.5–64.2%) | 36.1% (15.2–43.8%) | 36.7% (19.8–43.6%) |
| 200 | 54.9% (45.1–63.0%) | 63.1% (59.5–65.0%) | 38.9% (16.0–43.1%) | 38.5% (26.9–42.9%) |
| 400 | 54.9% (50.5–63.0%) | 63.7% (62.0–65.0%) | 39.4% (15.7–42.9%) | 39.0% (27.8–42.2%) |
| 800 | 55.0% (53.2–55.9%) | 63.5% (62.4–64.4%) | 39.4% (16.2–42.0%) | 39.0% (28.4–41.6%) |
| all 1,036 | 55.3% | 63.6% | 40.1% | 39.6% |
| untuned 0.5 | 49.4% | 63.1% | 12.6% | 12.6% |
| share of draws beating 0.5: n=50 / 200 / 800 | 74% / 90% / 100% | 18% / 50% / 66% | 84% / 99% / 100% | 85% / 99% / 100% |

Week 2 accuracy for Jev round 2 at n=50 ranges from 43.8% to 75.3% (5th–95th percentile).

## Hybrid (week 2; cut chosen on dev: 0.1 for every seed and both Jev settings)

| setup | accuracy | macro-F1 | in-scope answered | sent to Jev | not-allowed: caught by Jev / called irrelevant locally / **answered** / other |
|---|---|---|---|---|---|
| Jev alone, 0.5 | 53.3% | 49.4% | 24.8% | 100% | 190 / 0 / 2 / 72 |
| hybrid + Jev 0.5 (3 seeds) | 52.7–53.7% | 31.8–33.1% | 23.1–23.9% | 26.2–28.2% | 14–25 / 237–246 / 1–2 / 1–2 |
| Jev alone, week 1 thresholds | 61.3% | 55.3% | 46.6% | 100% | 184 / 0 / 2 / 78 |
| hybrid + Jev week 1 thresholds (3 seeds) | 57.8–58.7% | 37.3–38.9% | 44.4–45.3% | 26.2–28.2% | 14–24 / 237–246 / 1–2 / 1–2 |

The sweep is flat: from cut 0.1 to 0.9, the share sent to Jev moves only from about 28% to about 24%. The scope
scores are confident (near 0 or 1), so the cut hardly matters.

## Findings

1. **Tuning-set size mostly buys stability, not accuracy, for Jev.**
   - Median macro-F1 is about 55% whether thresholds are tuned on 50 or 800 questions.
   - The spread collapses: the 5th–95th percentile of accuracy is 44–75% at 50 questions and 57–62% at 800.
   - This explains the earlier 61.3% vs 75.5% swing for Jev round 2. Both are ordinary draws from that spread.
   - Any tuned number from a few hundred labelled questions is one draw, not a property of the model.
2. **With round 2b's order (in scope before ambiguous), Jev barely needs tuning.** Untuned 0.5 already gives 63.1%
   macro-F1. Tuned medians reach 63.5–63.7% only with 400+ questions, and at n=50 just 18% of draws beat 0.5. The
   decision rule mattered more than the thresholds. (2b is post hoc.)
3. **Zero-shot GLiNER can't be used without tuning, and stays fragile with it.**
   - At 0.5 it scores 12.6%.
   - It needs about 200 labelled questions before the median settles near 39%.
   - Even at 800, 5% of draws land near 16% (round 2) or 28% (round 2b). Its ambiguous and topic cuts are sensitive
     to which few examples are drawn.
4. **The local scope gate cuts Jev calls by about 72% without adding unsafe answers, but it hides the refusals.**
   - Not-allowed questions answered: 1–2, the same as Jev alone.
   - But 237–246 of 264 not-allowed questions are called irrelevant locally: refused politely with "I only cover
     company policy", with no topic logged. Macro-F1 drops from 55% to 37–39%, and the per-topic refusal log
     disappears.
   - Most not-allowed requests (harmful, privacy, legal advice) aren't HR-policy questions, so a scope gate
     naturally filters them out first.
5. **The gate doesn't solve the privacy problem; it inverts it.** What it keeps local is mostly off-topic chatter
   and not-allowed requests. What it sends to the API is the in-scope HR questions, which are where employees' own
   personal data lives.

## Caveats

- **One test week:** week 2 is a random half of the same pool, not later traffic.
- **The matched pairs are 30 in week 2,** too few for pair-level conclusions (not used here).
- **Round 2b is post hoc:** the ambiguity problem was first seen in week 2 results.
- **The local gate comes from a fine-tune whose topic and clarity parts collapsed.** Only its scope part is used,
  and that part works (ROC-AUC 0.99).
- **Jev's "week 1 thresholds" were tuned on all of week 1,** which includes the v2 dev set used to choose the cut.
- **Seed 42's tuned ambiguous threshold rests on floating-point noise.** Its clarity scores are 1 − 0.9999998, a
  tiny positive cut. The new fallback only catches exactly constant scores; a tolerance-based check would also
  catch near-constant ones.
- **Chart:** `results/calibration/curve.png` shows macro-F1 against tuning-set size.
  - Lines are medians; bands are the 5th–95th percentile.
  - Dashed lines are the untuned 0.5 cuts; hollow markers are tuned on all of week 1.
  - One panel per rule, on a shared y axis.

  The plot data is also in `curve.csv`.
