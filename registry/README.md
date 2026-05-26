# AACP — Agent Action Compression Protocol

**A pipe-delimited coordination protocol for multi-agent LLM systems.**

> Status: `v1.0-draft` · Benchmarks measured · Feedback welcome

---

## The Problem

When AI agents coordinate with each other they communicate in full natural language — verbose, ambiguous, and expensive to tokenise. Every inter-agent instruction is an API call. In multi-agent workflows with many hops, coordination overhead compounds.

**The same instruction, two ways:**

```
English (56 tokens on Claude):
"Please retrieve the employee salary records for the period ending
31 August 2024. I need all active employees, their departments,
cost centres, base salary, any changes made this month, and pension
contribution rates. Return as JSON array."

AACP v1.0 (48 tokens on Claude):
FETCH|HR|res:emp_salary|period:2024-08|filter:status=active|fields:id,dept,cc,base_sal,delta,pension_rate|fmt:json|return:HR-Agent|p:1|aacp:1.0
```

---

## Measured Results

Token counts measured from live API `usage_metadata`. Not estimated.
4 payroll workflow hops. Both Claude Sonnet 4.5 and GPT-4o.

| | English | AACP v1.0 | Delta |
|---|---|---|---|
| Claude Sonnet 4.5 | 240 tokens | ~188 tokens | **~22% reduction** |
| GPT-4o | 219 tokens | ~168 tokens | **~23% reduction** |

Consistent cross-model. Measured not estimated.

---

## What AACP Does

- Reduces coordination tokens by ~22% vs English (measured)
- Provides structured, unambiguous, machine-parseable instructions
- Enables deterministic zero-cost encoding for known workflows
- Validates every packet against a typed schema before transmission
- Creates clean structured audit trails
- Works on Claude, GPT-4o, and GPT-4.1

## What AACP Does Not Do

- Reduce task tokens (the work an agent performs — unchanged)
- Replace task-level instructions — only coordination messages
- Guarantee total workflow cost reduction without sufficient hop count

---

## Packet Format

```
TASK|DOM|res:RES|period:PERIOD|filter:FILTER|fields:FIELDS|fmt:FMT|return:AGENT|p:PRIORITY|aacp:VERSION
```

**Positional fields (0–9):**

| Position | Key | Required | Description |
|---|---|---|---|
| 0 | TASK | ✓ | Action: FETCH PROC FLAG RESOLVE LOG SEND BUILD MERGE CALC REPORT |
| 1 | DOM | ✓ | Domain: HR FIN SALES LEGAL IT CS MKT |
| 2 | res: | — | Resource identifier |
| 3 | period: | — | Time period |
| 4 | filter: | — | Filter expression |
| 5 | fields: | — | Comma-separated return fields |
| 6 | fmt: | — | Output format: json pdf xlsx csv |
| 7 | return: | ✓ | Receiving agent ID |
| 8 | p: | — | Priority: 1=critical 2=medium 3=low |
| 9 | aacp: | ✓ | Version tag: aacp:1.0 |

**Extended fields** (appended after position 9 as `|key:value`):
`src` `src_prev` `rules` `validate` `tmpl` `data_ptr` `amt` `ccy`
`sup` `match` `terms` `type` `party` `clause` `issue` `risk`
`block` `flags` `req` `highlight` `status` `to` `subj` `att`
`tone` `sentiment` `actor` `chain` `prog` `ltv` `loyalty` `urgency`

**Examples:**

```
# Fetch employee records
FETCH|HR|res:emp_salary|period:2024-08|filter:status=active|fields:id,dept,cc,base_sal|fmt:json|return:HR-Agent|p:1|aacp:1.0

# Process invoice
PROC|FIN|res:invoice||||fmt:json|return:FIN-Agent|p:2|aacp:1.0|sup:ABC-Ltd|amt:4200|ccy:GBP|match:PO-441|terms:net30

# Flag NDA clause
FLAG|LEGAL|||||  |return:LEG-Agent|p:1|aacp:1.0|type:NDA|party:Acme-Ltd|clause:s7|issue:ip_rights_restriction|risk:high|block:signature

# IT provisioning
BUILD|IT|res:ad_account||filter:usr=j.smith|fields:email,dept,grp,pwd_reset||return:IT-Agent|p:1|aacp:1.0
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
# FETCH|HR|res:emp_salary|period:2024-08|filter:status=active|...
print(f"Cost: ${pkt.api_cost_usd:.2f}")  # $0.00

# Validate any packet
from aacp import AACPValidator
v = AACPValidator()
result = v.validate(pkt.packet)
print(result.summary())

# Decode any packet to English
from aacp import AACPDecoder
d = AACPDecoder()
decoded = d.decode(pkt.packet)
print(decoded.english)

# Novel instructions — fallback to LLM, logged to registry
from aacp.encoders.fallback import FallbackEncoder
enc = FallbackEncoder()
pkt = enc.encode_english(
    english="Cross-reference new employee against background check DB.",
    domain="HR", return_agent="HR-Agent"
)
```

Run the demo (no API key needed):
```bash
python3 examples/demo.py
```

---

## Workflow Encoders

Pre-built zero-cost encoders for common business workflows:

| Encoder | Workflows | Hops |
|---|---|---|
| `PayrollEncoder` | Monthly payroll run | 6 |
| `ITEncoder` | New employee provisioning | 6 |
| `InvoiceEncoder` | AP invoice processing | 3 |
| `ContractEncoder` | Legal contract review | 3 |

For novel instructions: `FallbackEncoder` routes to LLM and logs the result
to `registry/unknown_patterns.json` as a future rule-based candidate.

---

## Relationship to Existing Protocols

| Protocol | Layer | What it does | AACP relationship |
|---|---|---|---|
| MCP (Anthropic/AAIF) | Tool access | Agent ↔ external system | AACP inside MCP payloads |
| A2A (Google/AAIF) | Coordination | Agent ↔ agent routing | AACP compresses A2A messages |
| Gibberlink/GGWave | Transport | Audio channel | Audio-specific; AACP is text-native |

AACP operates above transport protocols — inside message payloads, not at routing layer.

---

## Prior Work

The verbosity problem in agent communication is independently documented:

**EcoLANG** (Mou et al., Fudan University, May 2025, arXiv:2505.06904):
"There exists redundancy in current agent communication: when expressing
the same intention, agents tend to use lengthy and repetitive language."
EcoLANG achieved >20% token reduction through evolved compression language.

AACP targets business workflow coordination with a structured packet schema
rather than evolved natural language. Both address the same observed problem.

---

## Roadmap

| Version | Focus |
|---|---|
| `v1.0` (now) | Pipe-delimited format, rule-based encoders, measured benchmarks |
| `v1.1` | PyPI package (`pip install aacp`), TypeScript SDK |
| `v1.2` | Cross-model benchmark suite, persistent agent benchmarks |
| `v2.0` | Community encoding registry, IETF Internet-Draft |

---

## Contributing

Draft specification. Issues, PRs, and counter-proposals welcome.

```
/aacp         Python package
/benchmark    Benchmark harness
/benchmarks   Published results
/examples     Working demos
/registry     LLM fallback pattern log
```

---

## Licence

MIT — free to use, implement, extend, and fork.

*AACP is an independent protocol proposal. Not affiliated with Anthropic,
Google, IBM, or the Linux Foundation, though designed to complement their
respective protocol work (MCP, A2A, ACP).*
