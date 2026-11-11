# Policy Pal, frozen

Copied from [Policy Pal](https://github.com/lightshadow1/policy-pal) at commit `1194d41` ("Instrument Policy Pal with OTel GenAI tracing for audit
evidence"), so that the regex baseline is exactly what shipped. **Do not edit these files.**

- `guardrails.py`, `pii_scrubber.py`: `git show 1194d41:<file>`, byte for byte.
- `policies/*.txt`: the four policy documents at that commit.
- `retrieval.py`: `PolicyChunk`, `load_policies` and `find_relevant_policy`, copied verbatim from
  `policy_engine.py` (whose other imports, such as anthropic and OpenTelemetry, aren't needed here).

`tests/test_regex_guard.py` checks the two copied modules and the three `retrieval.py` ranges against the commit.
