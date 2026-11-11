# Second reviewer: GPT-6 vs Opus vs final labels

Both reviewers saw the same 858 judgment rows (the drafts as they were before review,
`data/review/external/inputs/`) and the same guide. Neither saw the other's review. GPT-6's files:
`data/review/external/output/gpt6_review.csv` and its notes.

## Agreement on the label (in_scope / irrelevant / not_allowed / ambiguous)

| | label | label + topic | Cohen's κ |
|---|---|---|---|
| GPT-6 vs Opus | 84.0% | 83.2% | 0.78 |
| GPT-6 vs final | 79.4% | 79.1% | 0.72 |
| Opus vs final | 91.3% | 91.3% | 0.88 |

Verdicts: GPT-6 642 agree / 122 change / 94 unsure; Opus 740 / 28 / 90.

**Where the reviewers disagree with the final labels.** On 54 rows both reviewers agree with each other but not
with the final label. All 54 are the user's own policy calls: 30 are the 401k rollover group (the user chose
not_allowed/investment, both reviewers said in_scope/covered=no), 23 come from the user's health and money rules
(the rule sweep), and 1 is another user group decision.

**Where GPT-6 differs most from the final labels:** it labels backstory-only StackExchange excerpts `ambiguous`
much more often (money 18 + 11, law 16 + 8, health 14, workplace 12), and keeps some general health and money
questions as not_allowed (health 17, money 11), as the guide read before the user's rules.

## Do the results depend on who labelled?

Week 2 accuracy, re-scored under each label set. Thresholds are re-tuned on week 1 under the same labels.

| guardrail | final labels | Opus-only labels | GPT-6 labels |
|---|---|---|---|
| regex | 26.5% | 27.3% | 27.7% |
| Jev round 1 | 33.1% | 32.8% | 32.6% |
| Jev round 2 (tuned) | 61.3% | 59.5% | 54.3% |
| **Jev round 2b (tuned)** | **70.3%** | **69.0%** | **68.2%** |
| GLiNER round 1 | 21.6% | 22.5% | 19.7% |
| GLiNER round 2 (tuned) | 48.1% | 48.3% | 48.3% |

Jev round 2b answers 88.0% / 87.1% / 89.6% of in-scope questions; GLiNER round 2 refuses 42.3% / 44.8% / 40.2% of
them; Jev catches 94.4% of privacy requests under all three label sets. The ranking and the conclusions don't
change. The largest swing is Jev round 2 under GPT-6 labels (−7 points), because GPT-6's extra `ambiguous` labels
reward that version's over-eager ambiguity check differently. Numbers: `results/review/label_sensitivity.json`.

## Guide issues both reviewers raised

- **Personal tax questions:** both raised them. GPT-6 would split "look up my total" (irrelevant) from "what do I
  legally owe" (legal).
- **Medical:** both found no academic carve-out. The user has since added one ("medical needs a personal case").
- **Self-harm disclosures:** Opus said harmful; GPT-6 said medical, and asked for a supportive crisis-response
  route rather than a refusal.
- **Missing intent in excerpts, and conversational filler:** both said the guide needs an explicit rule. GPT-6
  would make pure acknowledgements irrelevant rather than ambiguous.
