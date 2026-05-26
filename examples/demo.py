"""
AACP v1.0 Demo
Demonstrates pipe-delimited encoding across all workflow types.
No API key needed for this demo.

Usage:
    python3 examples/demo.py
    python3 examples/demo.py --fallback   # requires ANTHROPIC_API_KEY
"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from aacp.encoders.workflows.payroll import PayrollEncoder
from aacp.encoders.workflows.it_provisioning import ITEncoder
from aacp.encoders.workflows.finance_legal import InvoiceEncoder, ContractEncoder
from aacp import AACPValidator, AACPDecoder


def print_packet(label, pkt, validate=True, decode=False):
    v = AACPValidator()
    result = v.validate(pkt.packet)
    print(f"  [{label}]")
    print(f"    {pkt.packet}")
    status = "✓ VALID" if result.valid else "✗ INVALID"
    print(f"    {status} | encoder:{pkt.encoder_type.value} | cost:${pkt.api_cost_usd:.2f}")
    for w in result.warnings:
        print(f"    ⚠ {w}")
    if decode:
        d = AACPDecoder()
        decoded = d.decode(pkt.packet)
        print(f"    → {decoded.english[:100]}")
    print()


def run_demo():
    print("=" * 65)
    print("AACP v1.0 — PIPE-DELIMITED FORMAT DEMO")
    print("Measured ~22% token reduction vs English (Claude + GPT-4o)")
    print("=" * 65)

    # Payroll
    print("\nPAYROLL WORKFLOW")
    enc = PayrollEncoder()
    total = 0
    for label, pkt in [
        ("fetch employees",   enc.fetch_employees("2024-08")),
        ("fetch budgets",     enc.fetch_budgets("2024-08")),
        ("merge & calculate", enc.merge_and_calculate("2024-08")),
        ("generate report",   enc.generate_report("2024-08","2024-07")),
        ("log run",           enc.log_run("2024-08")),
        ("send report",       enc.send_report("2024-08")),
    ]:
        print_packet(label, pkt)
        total += 1
    print(f"  6 packets | 0 LLM calls | $0.00\n")

    # IT Provisioning
    print("IT PROVISIONING")
    it = ITEncoder()
    for label, pkt in [
        ("create AD account",  it.create_ad_account("j.smith","j.smith@co.com","Sales")),
        ("provision email",    it.provision_email("j.smith@co.com")),
        ("provision VPN",      it.provision_vpn("j.smith")),
        ("provision CRM",      it.provision_crm("j.smith")),
        ("provision badge",    it.provision_badge("j.smith")),
        ("log provisioning",   it.log_provisioning("j.smith")),
    ]:
        print_packet(label, pkt)
    print(f"  6 packets | 0 LLM calls | $0.00\n")

    # Finance & Legal
    print("FINANCE & LEGAL")
    inv = InvoiceEncoder()
    leg = ContractEncoder()
    for label, pkt in [
        ("process invoice",    inv.process_invoice("ABC Ltd",4200,"GBP","PO-441")),
        ("schedule payment",   inv.schedule_payment("ABC Ltd",4200,"GBP")),
        ("log invoice",        inv.log_invoice("INV-9921","ABC Ltd",4200,"GBP")),
        ("request NDA review", leg.request_review("NDA","Acme Ltd")),
        ("flag clause",        leg.flag_clause("NDA","Acme Ltd","s7","ip_rights_restriction")),
        ("log review",         leg.log_review("NDA","Acme Ltd","high","negotiate")),
    ]:
        print_packet(label, pkt)
    print(f"  6 packets | 0 LLM calls | $0.00\n")

    # Decode demo
    print("DECODE DEMO — pipe packet → English")
    d = AACPDecoder()
    packet = "FETCH|HR|res:emp_salary|period:2024-08|filter:status=active|fields:id,dept,cc,base_sal|fmt:json|return:HR-Agent|p:1|aacp:1.0"
    decoded = d.decode(packet)
    print(f"  Packet:  {packet}")
    print(f"  Decoded: {decoded.english}")
    print()

    # Validator demo
    print("VALIDATOR DEMO")
    v = AACPValidator()
    cases = [
        ("Valid packet",         "FETCH|HR|res:emp_salary|||fields:id,dept|fmt:json|return:HR-Agent|p:1|aacp:1.0"),
        ("Missing return",       "FETCH|HR|res:emp_salary||||fmt:json||p:1|aacp:1.0"),
        ("Unknown TASK",         "EXPLODE|HR|||||||return:HR-Agent|p:1|aacp:1.0"),
        ("SENTIMENT without TONE","RESOLVE|CS||||||||return:CS-Agent|p:1|aacp:1.0|sentiment:negative"),
    ]
    for label, pkt in cases:
        result = v.validate(pkt)
        status = "✓ VALID" if result.valid else "✗ INVALID"
        print(f"  {label}: {status}")
        for e in result.errors:   print(f"    ERROR: {e}")
        for w in result.warnings: print(f"    WARN:  {w}")
    print()

    if "--fallback" in sys.argv:
        run_fallback()
    else:
        print("Tip: run with --fallback to test LLM encoding (requires ANTHROPIC_API_KEY)")
        print("     python3 examples/demo.py --fallback\n")


def run_fallback():
    print("FALLBACK ENCODER — novel instructions")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("  ANTHROPIC_API_KEY not set — skipping\n")
        return
    from aacp.encoders.fallback import FallbackEncoder
    enc = FallbackEncoder(registry_dir="registry")
    for english, domain in [
        ("Cross-reference new employee against background check database before onboarding.", "HR"),
        ("Generate variance analysis comparing actual vs forecast payroll, flag lines over 5%.", "FIN"),
        ("Customer escalated to CEO. Prioritise above all others, prepare exec response within 1 hour.", "CS"),
    ]:
        print(f"  English: {english[:70]}...")
        result = enc.encode_english(english, domain, f"{domain}-Agent")
        print(f"  Packet:  {result.packet}")
        print(f"  Loss:    {result.compression_loss.value}")
        print()
    enc.print_registry_summary()


if __name__ == "__main__":
    run_demo()
