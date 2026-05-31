"""
AACP v1.3 — New Encoder Tests
Validates all four new workflow encoders.
No API calls. Pure packet validation.

Run from ~/Desktop/aacp-v1/:
  python3 tests/test_new_encoders.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aacp.encoders.workflows.sales          import SalesEncoder
from aacp.encoders.workflows.jml            import JMLEncoder
from aacp.encoders.workflows.customer_service import CSResolutionEncoder
from aacp.encoders.workflows.month_end      import MonthEndEncoder
from aacp.validator                         import AACPValidator

v = AACPValidator()
passed = failed = 0

def check(label, condition):
    global passed, failed
    if condition:
        print(f"  ✓ {label}")
        passed += 1
    else:
        print(f"  ✗ FAIL: {label}")
        failed += 1

def section(label):
    print(f"\n{'='*55}")
    print(f"  {label}")
    print(f"{'='*55}")

def validate_all(packets, label):
    for pkt in packets:
        r = v.validate(pkt.packet)
        check(f"{pkt.task}|{pkt.domain} validates", r.valid)
        if not r.valid:
            print(f"    Errors: {r.errors}")
            print(f"    Packet: {pkt.packet}")
        check(f"{pkt.task}|{pkt.domain} costs $0.00", pkt.api_cost_usd == 0.0)

# ── SalesEncoder ──────────────────────────────────────────────────────────────
section("SalesEncoder — Sales Qualification")
enc = SalesEncoder()

p1 = enc.fetch_lead("L-7712")
print(f"  {p1.packet}")
check("FETCH|SALES packet", p1.packet.startswith("FETCH|SALES|"))
check("lead id in filter", "id=L-7712" in p1.packet)

p2 = enc.score_lead("L-7712", framework="BANT")
print(f"  {p2.packet}")
check("CALC|SALES packet", p2.packet.startswith("CALC|SALES|"))
check("BANT rules present", "rules:bant" in p2.packet)

p3 = enc.route_lead("L-7712")
print(f"  {p3.packet}")
check("PROC|SALES packet", p3.packet.startswith("PROC|SALES|"))

p4 = enc.log_qualification("L-7712")
check("LOG|SALES packet", p4.packet.startswith("LOG|SALES|"))

p5 = enc.notify_rep("L-7712")
check("SEND|SALES packet", p5.packet.startswith("SEND|SALES|"))

full = enc.full_qualification("L-7712")
check("full qualification returns 5 packets", len(full) == 5)
validate_all(full, "SalesEncoder")

# ── JMLEncoder ────────────────────────────────────────────────────────────────
section("JMLEncoder — HR Onboarding / JML")
enc = JMLEncoder()

j1 = enc.fetch_new_hire("E009")
print(f"  {j1.packet}")
check("FETCH|HR packet", j1.packet.startswith("FETCH|HR|"))
check("employee id in filter", "id=E009" in j1.packet)

j2 = enc.create_account("j.smith", "Engineering")
print(f"  {j2.packet}")
check("BUILD|IT packet", j2.packet.startswith("BUILD|IT|"))
check("username in filter", "usr=j.smith" in j2.packet)

j3 = enc.assign_licences("j.smith", ["M365", "Slack"])
print(f"  {j3.packet}")
check("PROC|IT packet", j3.packet.startswith("PROC|IT|"))

j4 = enc.configure_access("j.smith")
check("BUILD|IT access packet", j4.packet.startswith("BUILD|IT|"))

j5 = enc.send_welcome("j.smith")
check("SEND|HR welcome", j5.packet.startswith("SEND|HR|"))

j6 = enc.log_provisioning("j.smith")
check("LOG|IT audit", j6.packet.startswith("LOG|IT|"))

# Mover
m1 = enc.update_access("j.smith", "senior_engineer")
print(f"  {m1.packet}")
check("PROC|IT mover packet", m1.packet.startswith("PROC|IT|"))
check("no_privilege_creep validation", "no_privilege_creep" in m1.packet)

# Leaver
l1 = enc.revoke_access("j.smith")
print(f"  {l1.packet}")
check("PROC|IT leaver packet", l1.packet.startswith("PROC|IT|"))

full_j = enc.full_joiner("E009", "j.smith", "Engineering")
check("full joiner returns 6 packets", len(full_j) == 6)
validate_all(full_j, "JMLEncoder")

# ── CSResolutionEncoder ───────────────────────────────────────────────────────
section("CSResolutionEncoder — Complaint Resolution")
enc = CSResolutionEncoder()

c1 = enc.fetch_customer("C-4421")
print(f"  {c1.packet}")
check("FETCH|CS packet", c1.packet.startswith("FETCH|CS|"))
check("customer id in filter", "id=C-4421" in c1.packet)

c2 = enc.triage_complaint("T-9912")
print(f"  {c2.packet}")
check("PROC|CS triage", c2.packet.startswith("PROC|CS|"))

c3 = enc.resolve_complaint("T-9912", sentiment="negative",
                            tone="empathetic", ltv=8000, goodwill=True)
print(f"  {c3.packet}")
check("RESOLVE|CS packet", c3.packet.startswith("RESOLVE|CS|"))
check("sentiment present", "sentiment:negative" in c3.packet)
check("tone present", "tone:empathetic" in c3.packet)
check("ltv present", "ltv:8000" in c3.packet)
check("goodwill in req", "goodwill_consider" in c3.packet)

c4 = enc.send_resolution("T-9912", "C-4421")
check("SEND|CS packet", c4.packet.startswith("SEND|CS|"))

c5 = enc.log_resolution("T-9912")
check("LOG|CS packet", c5.packet.startswith("LOG|CS|"))

full_c = enc.full_resolution("C-4421", "T-9912",
                              sentiment="negative", ltv=8000, goodwill=True)
check("full resolution returns 5 packets", len(full_c) == 5)
validate_all(full_c, "CSResolutionEncoder")

# ── MonthEndEncoder ───────────────────────────────────────────────────────────
section("MonthEndEncoder — Finance Month-End Close")
enc = MonthEndEncoder()

me1 = enc.fetch_trial_balance("2026-03")
print(f"  {me1.packet}")
check("FETCH|FIN trial balance", me1.packet.startswith("FETCH|FIN|"))
check("period present", "period:2026-03" in me1.packet)

me2 = enc.reconcile_bank("2026-03")
print(f"  {me2.packet}")
check("PROC|FIN bank recon", me2.packet.startswith("PROC|FIN|"))
check("gl_match validation", "gl_match" in me2.packet)

me3 = enc.post_accruals("2026-03")
print(f"  {me3.packet}")
check("CALC|FIN accruals", me3.packet.startswith("CALC|FIN|"))

me4 = enc.variance_analysis("2026-03", "2026-02")
print(f"  {me4.packet}")
check("CALC|FIN variance", me4.packet.startswith("CALC|FIN|"))
check("material variance highlight", "MATERIAL_VARIANCE" in me4.packet)

me5 = enc.generate_management_accounts("2026-03")
print(f"  {me5.packet}")
check("REPORT|FIN mgmt accounts", me5.packet.startswith("REPORT|FIN|"))

me6 = enc.log_close_certification("2026-03")
print(f"  {me6.packet}")
check("LOG|FIN certification", me6.packet.startswith("LOG|FIN|"))
check("certified status", "status:certified" in me6.packet)

full_me = enc.full_close("2026-03", "2026-02")
check("full close returns 6 packets", len(full_me) == 6)
validate_all(full_me, "MonthEndEncoder")

# ── All new packets validate ───────────────────────────────────────────────────
section("All packets from all new encoders")
all_packets = (
    enc.full_close("2026-03", "2026-02") +
    SalesEncoder().full_qualification("L-7712") +
    JMLEncoder().full_joiner("E009", "j.smith", "Engineering") +
    CSResolutionEncoder().full_resolution("C-4421", "T-9912")
)
all_valid = True
for pkt in all_packets:
    r = v.validate(pkt.packet)
    if not r.valid:
        print(f"  ✗ Invalid: {pkt.packet}")
        print(f"    {r.errors}")
        all_valid = False

check(f"all {len(all_packets)} new encoder packets validate", all_valid)
check(f"all {len(all_packets)} new encoder packets cost $0.00",
      all(p.api_cost_usd == 0.0 for p in all_packets))

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{'='*55}")
print(f"  RESULTS: {passed} passed, {failed} failed")
print(f"{'='*55}")
if failed == 0:
    print("\n  All new encoders validated. Ready for v1.3.\n")
else:
    sys.exit(1)
