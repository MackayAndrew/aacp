# AACP — Agent Action Compression Protocol

**A pipe-delimited coordination protocol for multi-agent LLM systems.**

> Status: `v1.1-draft` · Benchmarks measured · MIT Licensed · Feedback welcome
**IETF Internet-Draft:** [draft-mackay-aacp-00](https://datatracker.ietf.org/doc/draft-mackay-aacp/)

---

## The Problem

When AI agents coordinate with each other they communicate in full natural
language — verbose, ambiguous, and token-expensive. Every inter-agent
instruction is an API call. In multi-agent workflows with many hops,
coordination overhead compounds.

**The same instruction, two ways:**

```
English (56 tokens):
"Please retrieve the employee salary records for the period ending
31 August 2024. I need all active employees, their departments,
cost centres, base salary, any changes made this month, and pension
contribution rates. Return as JSON array."

AACP v1.1 (52 tokens):
FETCH|HR|return:HR-Agent|p:1|aacp:1.1|res:emp_salary|period:2024-08|filter:status=active|fmt:json
```

---

## Measured Results

Token counts measured from live API `usage_metadata`.
Not estimated. 4 payroll workflow hops. Claude Sonnet 4.5 and GPT-4o.
Bare coordination message only — no system prompt, no task content.

| Hop | English | AACP | Claude | GPT-4o |
|---|---|---|---|---|
| fetch employees | 56 | 52 | -7.1% | -12.7% |
| fetch budgets | 57 | 47 | -17.5% | -16.0% |
| merge calculate | 65 | 43 | -33.8% | -31.6% |
| generate report | 62 | 43 | -30.6% | -33.3% |
| **TOTAL** | **240** | **185** | **-22.9%** | **-23.7%** |

Consistent cross-model. All hops show reduction.

---

## What AACP Does

- Reduces coordination tokens by ~23% vs verbose English (measured)
- Provides structured, unambiguous, machine-parseable instructions
- Enables deterministic zero-cost encoding for known workflows
- Validates every packet against a typed schema before transmission
- Creates clean structured audit trails
- Works on Claude, GPT-4o, and GPT-4.1

## What AACP Does Not Do

- Reduce task tokens — the work an agent performs is unchanged
- Guarantee total workflow cost reduction without sufficient
  coordination-to-task token ratio
- Replace task-level instructions — only coordination messages

**Total workflow cost impact depends on your workflow type:**
Coordination-heavy workflows (IT provisioning, structured pipelines)
benefit most. Task-heavy workflows (contract review, open-ended research)
see less impact because task tokens dominate.

---

## Packet Format

```
TASK|DOM|return:AGENT|p:PRIORITY|aacp:VERSION|key:value|key:value...
```

TASK and DOM are positional (fields 0 and 1).
All other fields are named `key:value` pairs. No empty positional slots.

**Required:** `TASK` `DOM` `return:` `aacp:`
**Optional:** `res:` `period:` `filter:` `fields:` `fmt:` `p:`

**Valid TASK values:**
`FETCH` `PROC` `FLAG` `RESOLVE` `LOG` `SEND` `BUILD` `MERGE` `CALC` `REPORT` `ACK` `SYNC`

**Valid DOM values:**
`HR` `FIN` `SALES` `LEGAL` `IT` `CS` `MKT`

**Extended fields** (append as `|key:value` after core):
`src` `src_prev` `rules` `validate` `tmpl` `data_ptr` `amt` `ccy`
`sup` `match` `terms` `type` `party` `clause` `issue` `risk`
`block` `flags` `req` `highlight` `status` `to` `subj` `att`
`tone` `sentiment` `actor` `chain` `prog` `ltv` `loyalty` `urgency`

**Examples:**

```
# Fetch employee records
FETCH|HR|return:HR-Agent|p:1|aacp:1.1|res:emp_salary|period:2024-08|filter:status=active|fmt:json

# Merge and calculate
MERGE|HR|return:HR-Agent|p:1|aacp:1.1|rules:payroll_v2|validate:budget_cc

# Flag legal clause
FLAG|LEGAL|return:LEG-Agent|p:1|aacp:1.1|type:NDA|party:Acme-Ltd|clause:s7|issue:ip_rights_restriction|risk:high|block:signature

# IT provisioning
BUILD|IT|return:IT-Agent|p:1|aacp:1.1|res:ad_account|filter:usr=j.smith|fields:email,dept,grp,pwd_reset

# Process invoice
PROC|FIN|return:FIN-Agent|p:2|aacp:1.1|res:invoice|sup:ABC-Ltd|amt:4200|ccy:GBP|match:PO-441|terms:net30

# Resolve customer issue
RESOLVE|CS|return:CS-Agent|p:1|aacp:1.1|sentiment:negative|tone:empathetic|ltv:8000|ccy:GBP|req:goodwill_consider
```

---

## Quick Start

```bash
pip install -r requirements.txt
```

```python
# Zero-cost rule-based encoding for known workflows
from aacp.encoders.workflows.payroll import PayrollEncoder

enc = PayrollEncoder()
pkt = enc.fetch_employees(period="2024-08")
print(pkt.packet)
# FETCH|HR|return:HR-Agent|p:1|aacp:1.1|res:emp_salary|period:2024-08|filter:status=active|fmt:json
print(f"Cost: ${pkt.api_cost_usd:.2f}")  # $0.00

# Validate any packet
from aacp import AACPValidator
v = AACPValidator()
print(v.validate(pkt.packet).summary())

# Decode any packet to English
from aacp import AACPDecoder
d = AACPDecoder()
print(d.decode(pkt.packet).english)

# Novel instructions — fallback to LLM, logged to registry
from aacp.encoders.fallback import FallbackEncoder
enc = FallbackEncoder()
pkt = enc.encode_english(
    english="Cross-reference new employee against background check database.",
    domain="HR",
    return_agent="HR-Agent"
)
```

Run the demo (no API key needed):

```bash
python3 examples/demo.py
```

---

## Workflow Encoders

Pre-built zero-cost encoders for common business workflows.
Zero LLM calls. Deterministic output. $0.00 per packet.

| Encoder | Workflow | Packets |
|---|---|---|
| `PayrollEncoder` | Monthly payroll run | 6 |
| `ITEncoder` | New employee provisioning | 6 |
| `InvoiceEncoder` | AP invoice processing | 3 |
| `ContractEncoder` | Legal contract review | 3 |

For novel instructions: `FallbackEncoder` routes to LLM and logs
the result to `registry/unknown_patterns.json` as a future
rule-based candidate. One LLM call per novel pattern. Reused forever.

---

## Relationship to Existing Protocols

| Protocol | Layer | What it does | AACP relationship |
|---|---|---|---|
| MCP (Anthropic/AAIF) | Tool access | Agent ↔ external system | AACP inside MCP payloads |
| A2A (Google/AAIF) | Coordination | Agent ↔ agent routing | AACP compresses A2A messages |
| Gibberlink/GGWave | Transport | Audio channel | Audio-specific; AACP is text-native |

AACP fills the gap: semantic compression of coordination message
content. No existing protocol addresses this layer.

---

## Prior Work

**EcoLANG** (Mou et al., Fudan University, May 2025, arXiv:2505.06904)
independently identified agent communication verbosity as a problem
and achieved >20% token reduction through evolved compression language
for social simulation. AACP targets business workflow coordination
with a structured packet schema rather than evolved natural language.

---

## Design Notes

**Why pipe-delimited?**
Four formats were benchmarked (bracket `[KEY:VALUE]`, JSON, pipe,
abbreviated natural language). Pipe-delimited was the only format
achieving consistent token reduction on both Claude and GPT-4o
tokenisers. Bracket formats tokenise ~45% more expensively than
English due to `[`, `]`, `:` character overhead.

**Why keep field lists out of packets?**
Embedding field lists (`fields:id,dept,cc,base_sal`) inflates
coordination tokens significantly. A well-configured persistent
agent knows its default return fields. The packet communicates
intent; the agent's system prompt carries the schema.

**Why not URI data pointers?**
`://` and `/` in URIs tokenise very inefficiently. Data references
belong in agent working memory, not in coordination messages.

---

## Benchmarks

```bash
export ANTHROPIC_API_KEY=...
export OPENAI_API_KEY=...
python3 benchmark/tokenisation_test.py
```

All benchmark results published in `benchmarks/`.
Raw JSON files available for independent verification.

---

## Roadmap

| Version | Status | Focus |
|---|---|---|
| v1.0 | Released | Pipe-delimited format, rule-based encoders, working SDK |
| v1.1 | Released | Validated benchmarks — -22.9% Claude, -23.7% GPT-4o |
| v1.2 | Planned | PyPI package (`pip install aacp`), TypeScript SDK |
| v2.0 | Planned | IETF Internet-Draft, community encoding registry |

---

## Contributing

Draft specification. Issues, PRs, and counter-proposals welcome.

```
aacp/           Python package — encoder, decoder, validator
benchmark/      Benchmark harness and tokenisation tests
benchmarks/     Published results (JSON + summary)
examples/       Working demos
registry/       LLM fallback pattern log
```

---

## Licence

MIT — free to use, implement, extend, and fork.

*AACP is an independent protocol proposal. Not affiliated with
Anthropic, Google, IBM, or the Linux Foundation, though designed
to complement their respective protocol work (MCP, A2A, ACP).*
