# AACP — Agent Action Compression Protocol

[![PyPI version](https://badge.fury.io/py/aacp.svg)](https://pypi.org/project/aacp/)
[![npm version](https://badge.fury.io/js/aacp-ts.svg)](https://www.npmjs.com/package/aacp-ts)

**A pipe-delimited coordination protocol for multi-agent LLM systems.**

> Status: `v1.1-draft` · Benchmarks measured · MIT Licensed · Feedback welcome

**IETF Internet-Draft:** [draft-mackay-aacp-01](https://datatracker.ietf.org/doc/draft-mackay-aacp/)
**Working lab:** [github.com/MackayAndrew/aacp-lab](https://github.com/MackayAndrew/aacp-lab) — 4-model payroll workflow with Excel output
**TypeScript SDK:** [github.com/MackayAndrew/aacp-ts](https://github.com/MackayAndrew/aacp-ts) — `npm install aacp-ts`
**Community Rules:** [github.com/MackayAndrew/aacp-community-rules](https://github.com/MackayAndrew/aacp-community-rules) — 241 validated rules across 7 domains

---

## What AACP Does

AACP transforms verbose natural language agent-to-agent instructions
into deterministic, auditable coordination packets. Structured. Typed.
Validated. Open.

For known workflow types, a rule-based encoder produces AACP packets
deterministically at zero LLM cost. A three-tier fallback encoder
handles novel instructions: exact matches served from registry cache
at $0.00, pattern matches at $0.00, novel instructions encoded via
LLM and logged -- one LLM call per novel pattern, reused indefinitely.

---

## Install

```bash
# Python
pip install aacp

# TypeScript / JavaScript
npm install aacp-ts
```

---

## The Problem

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
Not estimated. 4-hop payroll workflow. May 2026.

| Hop | English | AACP | Claude | GPT-4o |
|---|---|---|---|---|
| fetch employees | 56 | 52 | -7.1% | -12.7% |
| fetch budgets | 57 | 47 | -17.5% | -16.0% |
| merge calculate | 65 | 43 | -33.8% | -31.6% |
| generate report | 62 | 43 | -30.6% | -33.3% |
| **TOTAL** | **240** | **185** | **-22.9%** | **-23.7%** |

---

## Quick Start (Python)

```python
# Zero-cost rule-based encoding for known workflows
from aacp.encoders.workflows.payroll import PayrollEncoder

enc = PayrollEncoder()
pkt = enc.fetch_employees(period="2026-03")
print(pkt.packet)
# FETCH|HR|return:HR-Agent|p:1|aacp:1.1|res:emp_salary|period:2026-03|filter:status=active|fmt:json
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
    english="Cross-reference contractors against the approved vendor list.",
    domain="FIN",
    return_agent="FIN-Agent"
)
# First call: LLM, ~$0.0006
# Every subsequent identical call: $0.00 from registry cache
```

## Quick Start (TypeScript)

```typescript
import { PayrollEncoder, AACPValidator, AACPDecoder } from "aacp-ts";

const enc = new PayrollEncoder();
const pkt = enc.fetchEmployees("2026-03");
console.log(pkt.packet);
// FETCH|HR|return:HR-Agent|p:1|aacp:1.1|res:emp_salary|period:2026-03|filter:status=active|fmt:json
console.log(pkt.apiCostUsd); // 0

const v = new AACPValidator();
console.log(v.validate(pkt.packet).valid); // true

const d = new AACPDecoder();
console.log(d.decode(pkt.packet).english);
```

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

**Examples:**

```
# Fetch employee records
FETCH|HR|return:HR-Agent|p:1|aacp:1.1|res:emp_salary|period:2026-03|filter:status=active|fmt:json

# Merge and calculate payroll
MERGE|HR|return:HR-Agent|p:1|aacp:1.1|rules:payroll_v2|validate:budget_cc

# Flag legal clause
FLAG|LEGAL|return:LEG-Agent|p:1|aacp:1.1|type:NDA|party:Acme-Ltd|clause:s7|issue:ip_rights_restriction|risk:high|block:signature

# Build IT account
BUILD|IT|return:IT-Agent|p:1|aacp:1.1|res:ad_account|filter:usr=j.smith|fields:email,dept,grp,pwd_reset

# Process invoice
PROC|FIN|return:FIN-Agent|p:2|aacp:1.1|res:invoice|sup:ABC-Ltd|amt:4200|ccy:GBP|match:PO-441|terms:net30
```

---

## Workflow Encoders

Pre-built zero-cost encoders for common business workflows.
Available in both Python and TypeScript.

| Encoder | Workflow | Hops |
|---|---|---|
| `PayrollEncoder` | Monthly payroll run | 6 |
| `ITEncoder` | New employee provisioning | 5–6 |
| `InvoiceEncoder` | AP invoice processing | 3 |
| `ContractEncoder` | Legal contract review | 2–3 |

---

## Tooling

**Dispatch — VS Code Extension**
Syntax highlighting, live validation, hover decode, autocomplete,
and token count for AACP packets in `.aacp` files and inline in
Python, TypeScript, and JavaScript.

Install: [marketplace.visualstudio.com](https://marketplace.visualstudio.com/items?itemName=dispatch-aacp.dispatch-aacp)
or search "Dispatch AACP" in the VS Code Extensions panel.

**Dispatch — Web Builder**
Browser-based packet builder and validator.
Build packets with dropdowns, validate instantly, share via URL.

[dispatch.aacp.dev](https://dispatch.aacp.dev)

---

## Three-Tier Fallback Encoder

```
Tier 1 — Hash cache
  Exact same instruction seen before → cached packet → $0.00

Tier 2 — Pattern match
  Similar instruction matches registry or built-in → $0.00

Tier 3 — LLM fallback
  Novel instruction → LLM call → logged to registry → ~$0.0006
  Same instruction next time → Tier 1 → $0.00
```

One LLM call per novel pattern. Reused indefinitely.

---

## Multi-Model Lab Results

4-model comparison on a 5-hop Q1 FY2026 payroll workflow.
All four models correctly interpreted AACP v1.1 packets.

| Model | Cost | Tokens in | Latency | Success |
|---|---|---|---|---|
| gpt-4.1-mini | $0.0044 | 7,566 | 82.5s | ✓ |
| gpt-4.1 | $0.0224 | 7,673 | 39.4s | ✓ |
| claude-sonnet-4-5 | $0.0416 | 9,062 | 77.5s | ✓ |
| gpt-4o | $0.0552 | 7,615 | 31.6s | ✓ |

Lab: [github.com/MackayAndrew/aacp-lab](https://github.com/MackayAndrew/aacp-lab)

---

## Relationship to Existing Protocols

| Protocol | Layer | AACP relationship |
|---|---|---|
| MCP (Anthropic/AAIF) | Tool access | AACP inside MCP payloads |
| A2A (Google/AAIF) | Agent routing | AACP compresses A2A messages |
| Gibberlink/GGWave | Audio transport | Audio-specific; AACP is text-native |

AACP fills the coordination content layer -- no existing protocol
addresses this specific layer.

---

## Benchmarks

```bash
export ANTHROPIC_API_KEY=...
export OPENAI_API_KEY=...
python3 benchmark/tokenisation_test.py
```

Raw JSON results in `benchmarks/`. Total API cost to build and
validate the entire protocol: under $2.00.

---

## Roadmap

| Version | Status | Focus |
|---|---|---|
| v1.0 | Released | Pipe-delimited format, rule-based encoders |
| v1.1 | Released | Validated benchmarks — -22.9% Claude, -23.7% GPT-4o |
| v1.2 | Released | Fallback loop closed, PyPI + npm, IETF draft-01, TS SDK |
| v1.3 | Planned | Additional workflow encoders, amortisation benchmark |
| v2.0 | Planned | IETF draft-02, community encoding registry |

---

## Contributing

Draft specification. Issues, PRs, and counter-proposals welcome.

```
aacp/               Python package
benchmark/          Benchmark harness
benchmarks/         Published results
examples/           Working demos
registry/           LLM fallback pattern log
tests/              Fallback loop tests
```

---

## Licence

MIT — free to use, implement, extend, and fork.

*AACP is an independent protocol proposal. Not affiliated with
Anthropic, Google, IBM, or the Linux Foundation, though designed
to complement MCP, A2A, and ACP.*
