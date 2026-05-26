"""
AACP v1.0 Tokenisation Benchmark
Measures actual token counts for AACP v1.0 pipe-delimited packets
vs equivalent English instructions.

This is the test that validated the format choice.
Results: Format C (pipe-delimited) achieves ~22% reduction on both
Claude and GPT-4o tokenisers.

Usage:
    export ANTHROPIC_API_KEY=...
    export OPENAI_API_KEY=...       # optional
    python3 benchmark/tokenisation_test.py
"""
import os, sys, time, json
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import anthropic

PAYROLL_PAIRS = [
    {
        "id": "hop_1_fetch_employees",
        "english": (
            "Please retrieve the employee salary records for the period ending "
            "31 August 2024. I need all active employees, their departments, "
            "cost centres, base salary, any changes made this month, and pension "
            "contribution rates. Return as JSON array."
        ),
        "aacp": "FETCH|HR|res:emp_salary|period:2024-08|filter:status=active|fields:id,dept,cc,base_sal,delta,pension_rate|fmt:json|return:HR-Agent|p:1|aacp:1.0",
    },
    {
        "id": "hop_2_fetch_budgets",
        "english": (
            "I now have the payroll data from HRMS. I need you to provide the "
            "budget allocations by cost centre so I can verify that payroll costs "
            "fall within approved budgets before we proceed. Please include "
            "year-to-date spend."
        ),
        "aacp": "FETCH|FIN|res:budget_cc|period:2024-08||fields:cc_id,approved_budget,ytd_spend|fmt:json|return:HR-Agent|p:1|aacp:1.0",
    },
    {
        "id": "hop_3_merge_calculate",
        "english": (
            "I have both employee salary data and budget allocations. "
            "Please merge these datasets, apply pension contribution rates, "
            "calculate net pay for all employees, apply PAYE deductions, "
            "validate totals against approved budgets, and flag any anomalies. "
            "Use payroll rules version 2."
        ),
        "aacp": "MERGE|HR|||||| |return:HR-Agent|p:1|aacp:1.0|src:hrms://emp/2024-08,fin://budget_cc/2024-08|rules:payroll_v2|validate:budget_cc",
    },
    {
        "id": "hop_4_generate_report",
        "english": (
            "Payroll calculation is complete. Please generate the monthly payroll "
            "report using the standard payroll monthly template. Include a summary "
            "page, department breakdown, anomaly flags, and produce it in both PDF "
            "and Excel format. Include comparison to last month."
        ),
        "aacp": "REPORT|HR||||| |fmt:pdf,xlsx|return:HR-Agent|p:2|aacp:1.0|src:pay://run/2024-08|src_prev:pay://run/2024-07|tmpl:payroll_monthly|highlight:REVIEW_REQ",
    },
]


def measure_claude(texts):
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    results = {}
    for label, text in texts:
        r = client.messages.create(
            model="claude-sonnet-4-5", max_tokens=1,
            messages=[{"role":"user","content":text}]
        )
        results[label] = r.usage.input_tokens
        time.sleep(0.3)
    return results


def measure_openai(texts, model="gpt-4o"):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    except ImportError:
        return {}
    results = {}
    for label, text in texts:
        r = client.chat.completions.create(
            model=model, max_tokens=1,
            messages=[{"role":"user","content":text}]
        )
        results[label] = r.usage.prompt_tokens
        time.sleep(0.3)
    return results


def run():
    print("=" * 60)
    print("AACP v1.0 TOKENISATION BENCHMARK")
    print("Pipe-delimited format vs English baseline")
    print("=" * 60)

    english_texts = [(h["id"], h["english"]) for h in PAYROLL_PAIRS]
    aacp_texts    = [(h["id"], h["aacp"])    for h in PAYROLL_PAIRS]

    print("\nClaude Sonnet 4.5:")
    c_eng = measure_claude(english_texts)
    c_pkt = measure_claude(aacp_texts)

    has_openai = bool(os.environ.get("OPENAI_API_KEY"))
    o_eng, o_pkt = {}, {}
    if has_openai:
        print("GPT-4o:")
        o_eng = measure_openai(english_texts)
        o_pkt = measure_openai(aacp_texts)

    print(f"\n{'Hop':<30} {'C-Eng':>6} {'C-AACP':>7} {'C-Delta':>9}", end="")
    if has_openai: print(f" {'O-Eng':>6} {'O-AACP':>7} {'O-Delta':>9}", end="")
    print()
    print("-" * (60 + (32 if has_openai else 0)))

    c_eng_total = c_pkt_total = 0
    o_eng_total = o_pkt_total = 0

    for h in PAYROLL_PAIRS:
        hid = h["id"].replace("hop_","").replace("_"," ")[:28]
        ce = c_eng.get(h["id"],0)
        cp = c_pkt.get(h["id"],0)
        cd = ((cp-ce)/ce*100) if ce else 0
        c_eng_total += ce; c_pkt_total += cp
        print(f"  {hid:<28} {ce:>6} {cp:>7} {cd:>+8.1f}%", end="")
        if has_openai:
            oe = o_eng.get(h["id"],0)
            op = o_pkt.get(h["id"],0)
            od = ((op-oe)/oe*100) if oe else 0
            o_eng_total += oe; o_pkt_total += op
            print(f" {oe:>6} {op:>7} {od:>+8.1f}%", end="")
        print()

    print("-" * (60 + (32 if has_openai else 0)))
    cd_total = ((c_pkt_total-c_eng_total)/c_eng_total*100) if c_eng_total else 0
    print(f"  {'TOTAL':<28} {c_eng_total:>6} {c_pkt_total:>7} {cd_total:>+8.1f}%", end="")
    if has_openai:
        od_total = ((o_pkt_total-o_eng_total)/o_eng_total*100) if o_eng_total else 0
        print(f" {o_eng_total:>6} {o_pkt_total:>7} {od_total:>+8.1f}%", end="")
    print()

    print(f"\nFINDING:")
    if cd_total < 0:
        print(f"  AACP v1.0 (pipe-delimited) reduces coordination tokens")
        print(f"  by {abs(cd_total):.1f}% on Claude vs English equivalent.")
        if has_openai and od_total < 0:
            print(f"  GPT-4o: {abs(od_total):.1f}% reduction — consistent cross-model.")
    else:
        print(f"  AACP v1.0 uses {cd_total:.1f}% MORE tokens than English on Claude.")
        print(f"  Review packet construction — empty fields may be inflating count.")

    # Save
    Path("benchmarks").mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "format": "aacp_v1_pipe_delimited",
        "claude": {
            "english_total": c_eng_total, "aacp_total": c_pkt_total,
            "delta_pct": round(cd_total,1),
        },
        "openai": {
            "english_total": o_eng_total, "aacp_total": o_pkt_total,
            "delta_pct": round(od_total,1) if has_openai else None,
        } if has_openai else None,
        "caveat": "Token counts from live API usage_metadata. Bare user message only.",
    }
    path = f"benchmarks/tokenisation_{ts}.json"
    with open(path,"w") as f: json.dump(out, f, indent=2)
    print(f"\nSaved: {path}")


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: set ANTHROPIC_API_KEY"); sys.exit(1)
    run()
