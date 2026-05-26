# AACP v1.0 Benchmark Summary

> All token counts measured from live API usage_metadata.
> No word-count estimates used anywhere in this document.

---

## Format Selection — Why Pipe-Delimited

Four formats were benchmarked before settling on the pipe-delimited design.
All measurements are from live API calls, bare user message, max_tokens=1.

```
FORMAT COMPARISON — 4 PAYROLL HOPS (coordination messages only)
────────────────────────────────────────────────────────────────
Format                         Claude tokens   GPT-4o tokens   Delta (Claude)
────────────────────────────────────────────────────────────────
English (baseline)                       240             219   —
[KEY:VALUE] bracket format               348             287   +45.0%
Minimal JSON                             273             249   +13.8%
Pipe-delimited (selected)                188             168   -21.7%
Abbreviated natural language             208             183   -13.3%
────────────────────────────────────────────────────────────────
```

**Finding:** Bracket-heavy formats (`[KEY:VALUE]`) tokenise inefficiently —
each `[`, `]`, `:` consumes tokens. Pipe characters tokenise more efficiently,
producing genuine reduction on both Claude and GPT-4o tokenisers.

Interpretability scores (Claude — proportion of expected output fields returned):
English: 0.88 | JSON: 0.54 | Pipe: 0.54 | Abbrev: 0.54

Pipe-delimited selected: best token reduction, passes interpretability, consistent cross-model.

---

## AACP v1.0 Tokenisation Results

Payroll workflow — 4 coordination hops.
Claude Sonnet 4.5 and GPT-4o.

```
HOP-LEVEL TOKEN COUNTS (Claude Sonnet 4.5)
─────────────────────────────────────────────────────
Hop                         English   AACP v1.0   Delta
─────────────────────────────────────────────────────
1  fetch employees               56          48   -14.3%
2  fetch budgets                 57          42   -26.3%
3  merge & calculate             65          48   -26.2%
4  generate report               62          50   -19.4%
─────────────────────────────────────────────────────
TOTAL                           240         188   -21.7%

GPT-4o:
TOTAL                           219         168   -23.3%
```

Consistent cross-model. Both tokenisers show similar reduction.

---

## What These Numbers Mean

**Coordination token reduction of ~22% is real and measured.**

However: AACP only compresses coordination messages — the instructions agents
send each other. Task tokens (the actual work: reading documents, generating
reports, analysing data) are unchanged.

Total workflow cost reduction depends on the ratio of coordination to task tokens:

| Workflow type | Coordination share | Expected total saving |
|---|---|---|
| IT provisioning (pure coordination) | ~40% | ~8-9% |
| Payroll run (mixed) | ~20% | ~4-5% |
| Contract review (task-heavy) | ~5% | ~1% |

---

## Interpretability

All tested models (Claude Sonnet 4.5, GPT-4o, GPT-4.1) correctly interpreted
AACP v1.0 pipe-delimited packets without protocol training. Zero failed completions.

Score methodology: proportion of expected output fields mentioned in agent response.
Pass threshold: 0.50. All non-English formats scored 0.54.

---

## Reproducing

```bash
git clone https://github.com/MackayAndrew/aacp
cd aacp
pip3 install -r requirements.txt
export ANTHROPIC_API_KEY=...
export OPENAI_API_KEY=...      # optional, for cross-model
python3 benchmark/tokenisation_test.py
```

---

## Methodology Notes

- Bare user message only — no system prompt, no task content
- max_tokens=1 to minimise output cost
- Token counts from API usage_metadata, not estimated
- 0.3s delay between calls to avoid rate limits
- Results saved as timestamped JSON in benchmarks/
