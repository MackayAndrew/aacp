# AACP Benchmarks

All token counts measured from live API usage_metadata.
No word-count estimates used anywhere in this directory.

## Running

    export ANTHROPIC_API_KEY=...
    export OPENAI_API_KEY=...
    python3 benchmark/tokenisation_test.py

## Key result

AACP v1.1 pipe-delimited format achieves:
  -22.9% coordination token reduction vs English (Claude Sonnet 4.5)
  -23.7% coordination token reduction vs English (GPT-4o)

Measured May 2026. 4 payroll workflow hops.
Bare coordination message only — no system prompt, no task content.

## Methodology

- Bare user message, no system prompt, max_tokens=1
- Token counts from API usage_metadata not estimated
- English baseline is the full verbose instruction AACP replaces
- 0.3s delay between calls to avoid rate limits
- Results saved as timestamped JSON files
