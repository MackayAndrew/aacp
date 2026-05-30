"""
AACP v1.2 — Fallback Loop Test
Exercises all three tiers:
  Tier 1: Hash match  (exact repeat → cached, $0.00)
  Tier 2: Pattern match (registry or builtin → $0.00)
  Tier 3: LLM fallback (novel → LLM call, logged)

Run from ~/Desktop/aacp-v1/:
  python3 tests/test_fallback_loop.py

Requires: ANTHROPIC_API_KEY set
Cleans up test registry after run.
"""

import sys, os, shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aacp.encoders.fallback import FallbackEncoder

TEST_REGISTRY = "registry_test"


def sep(label):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")


def run():
    enc = FallbackEncoder(registry_dir=TEST_REGISTRY, log_fallbacks=True)

    # ── Test 1: Novel instruction → should hit LLM (Tier 3) ──────────────────
    sep("TEST 1 — Novel instruction (expect: LLM fallback)")

    novel = (
        "Cross-reference all contractors against the approved vendor "
        "list and flag any without a valid purchase order for Q2 2026."
    )
    r1 = enc.encode_english(novel, domain="FIN",
                             return_agent="FIN-Agent", priority="2")
    print(f"  Packet:  {r1.packet}")
    print(f"  Cost:    ${r1.api_cost_usd:.4f}")
    print(f"  Encoder: {r1.encoder_type}")

    assert r1.packet, "No packet returned"
    assert r1.api_cost_usd > 0, "Should have cost — LLM was called"
    print("  PASS")

    # ── Test 2: Exact same instruction → should hit registry cache (Tier 1) ───
    sep("TEST 2 — Same instruction again (expect: hash_match, $0.00)")

    r2 = enc.encode_english(novel, domain="FIN",
                             return_agent="FIN-Agent", priority="2")
    print(f"  Packet:  {r2.packet}")
    print(f"  Cost:    ${r2.api_cost_usd:.4f}")
    print(f"  Encoder: {r2.encoder_type}")

    assert r2.packet == r1.packet, "Cached packet should match original"
    assert r2.api_cost_usd == 0.0, "Should be $0.00 — served from cache"
    assert r2.encoder_type.value == "rule_based", "Should show as rule_based"
    print("  PASS — loop closed, $0.00 on repeat")

    # ── Test 3: Builtin keyword match ─────────────────────────────────────────
    sep("TEST 3 — Builtin keyword match (expect: pattern hit)")

    builtin_match = "Please retrieve the employee salary records for September 2026"
    r3 = enc.encode_english(builtin_match, domain="HR",
                             return_agent="HR-Agent", priority="1")
    print(f"  Packet:  {r3.packet}")
    print(f"  Encoder: {r3.encoder_type}")
    assert r3.packet, "No packet returned"
    print("  PASS")

    # ── Test 4: Registry summary ───────────────────────────────────────────────
    sep("TEST 4 — Registry summary")
    enc.print_registry_summary()

    # ── Test 5: Third repeat → still hits cache ───────────────────────────────
    sep("TEST 5 — Third repeat (expect: hash_match, times_seen increments)")

    r5 = enc.encode_english(novel, domain="FIN",
                             return_agent="FIN-Agent", priority="2")
    assert r5.api_cost_usd == 0.0
    assert r5.loss_note and "registry" in r5.loss_note.lower()
    print(f"  Cost:    ${r5.api_cost_usd:.4f}")
    print(f"  Note:    {r5.loss_note}")
    print("  PASS")

    sep("ALL TESTS PASSED")
    print(f"\n  The fallback loop is closed.")
    print(f"  Novel instruction: 1 LLM call")
    print(f"  Every repeat after: $0.00")


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: set ANTHROPIC_API_KEY")
        sys.exit(1)
    try:
        run()
    finally:
        if os.path.exists(TEST_REGISTRY):
            shutil.rmtree(TEST_REGISTRY)
            print(f"\n  Cleaned up {TEST_REGISTRY}/")
