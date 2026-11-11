# Policy Pal guardrails

An evaluation of input guardrails for [Policy Pal](https://github.com/lightshadow1/policy-pal), an internal
assistant that answers HR and IT policy questions. Three guardrails are compared on a 2,091-question test set:

- **Regex:** Policy Pal's guardrail as shipped, frozen unchanged in `vendor/policypal/`.
- **Jev** (TypeSafe), given plain-English topic definitions.
- **GLiNER2.5-Decide** base, zero-shot, given label descriptions.

Every question has one of four labels: in scope, irrelevant, not allowed (with a topic) or ambiguous. The set is
split into two "weeks of traffic":

- **Week 1** (1,036 questions) is for review and threshold tuning.
- **Week 2** (1,055) is held out for the final numbers.

There are three rounds of definitions:

- **Round 1** uses the day-one topics.
- **Round 2** adds the topics that reviewing week 1 showed were missing.
- **Round 2b** (post hoc) checks in scope before ambiguous.

## Results (week 2)

| guardrail | accuracy (95% CI) | macro-F1 | labelled data used |
|---|---|---|---|
| Regex, as shipped | 26.5% (23.9–29.2%) | 14.9% | none |
| Jev, round 2, threshold 0.5 | 53.3% (50.3–56.1%) | 49.4% | none |
| Jev, round 2, tuned | 61.3% (58.4–64.1%) | 55.3% | ~1,000 week 1 questions |
| Jev, round 2b, tuned *(post hoc)* | 70.3% (67.4–73.0%) | 63.6% | ~1,000 week 1 questions |
| GLiNER, round 2, tuned | 48.1% (44.9–51.1%) | 40.1% | ~1,000 week 1 questions |

- **Full tables:** `results/report.md`.
- **Findings and decisions:** `docs/2026-10-29-summary.md`.
- **Fine-tune:** `docs/2026-11-04-finetune.md`, a LoRA fine-tune of GLiNER on the four labels. Its topic part
  collapsed.
- **Calibration and hybrid:** `docs/2026-11-05-calibration-hybrid.md`. It covers how many labelled questions
  threshold tuning needs, and tests a local scope gate in front of Jev.

## Layout

| path | what |
|---|---|
| `ppguard/` | build, scoring, decision rule, tuning, metrics, reports, fine-tune data, calibration |
| `data/testset.jsonl`, `data/labels.csv` | the test set and its labels; `data/labelling_guide.md` has the rules |
| `data/review/` | label reviews by two other models (Opus, GPT-6), with the prompt and inputs sent |
| `data/train/`, `data/finetune*/` | generated training questions (labelled blind by a second model) and fine-tune data |
| `finetune/` | GPU scripts for the GLiNER LoRA fine-tune (run over ssh in a Docker image) |
| `results/` | reports, review material, fine-tune and calibration outputs |
| `vendor/policypal/` | Policy Pal's guardrail and policies, frozen at commit `1194d41` |

## Running

```
uv sync
uv run pytest                                          # offline, no credentials
uv run python -m ppguard.runner --guard jev --round 2  # needs TYPESAFE_API_KEY in .env (see .env.example)
uv run python -m ppguard.report --round 2              # writes results/report.md
```

Scores are cached in `results/cache/`, which isn't in the repo. Rerun `ppguard.runner` before running the report
or `ppguard.calibration`. GLiNER scoring needs a GLiNER2.5-Decide service at `GLINER_ENDPOINT`.

## Data sources and licences

The code is MIT-licensed (`LICENSE`). The data keeps its sources' licences:

| source | rows | licence |
|---|---|---|
| [CLINC150](https://huggingface.co/datasets/clinc/clinc_oos) | 790 | CC BY 3.0 |
| [Aegis 2.0](https://huggingface.co/datasets/nvidia/Aegis-AI-Content-Safety-Dataset-2.0) | 350 | CC BY 4.0 |
| Stack Exchange excerpts (Workplace, Law, Health, Money, Super User, Ask Ubuntu), via [stack-exchange-preferences](https://huggingface.co/datasets/HuggingFaceH4/stack-exchange-preferences) | 460 | CC BY-SA 4.0 |
| [XSTest](https://huggingface.co/datasets/Paul/XSTest) | 150 | CC BY 4.0 |
| [CoCoNot](https://huggingface.co/datasets/allenai/coconot) | 80 | ODC-BY |
| [deepset prompt-injections](https://huggingface.co/datasets/deepset/prompt-injections) | 60 | Apache 2.0 |
| Written for this project (matched pairs, Policy Pal's own test questions) | 201 | this repo |

Each row's `source` and `licence` fields are in `data/testset.jsonl`. The Stack Exchange excerpts are the first one
to three sentences of each question, shared under CC BY-SA 4.0. Aegis, XSTest and CoCoNot rows include harmful or
offensive requests; they are here to test refusals. The personal details in Policy Pal's questions (emails, SSNs,
card numbers) are made-up test values.
