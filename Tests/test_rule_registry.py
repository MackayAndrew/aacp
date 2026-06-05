"""
AACP v1.4 — RuleRegistry Tests
Tests from_file() (no internet needed) and search functionality.

Run from ~/Desktop/aacp-v1/:
  python3 tests/test_rule_registry.py
"""

import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aacp.registry import RuleRegistry

passed = failed = 0

def check(label, condition):
    global passed, failed
    if condition:
        print(f"  ✓ {label}")
        passed += 1
    else:
        print(f"  ✗ FAIL: {label}")
        failed += 1

print("\n" + "="*55)
print("  RuleRegistry Tests")
print("="*55)

# Create a minimal test index
test_rules = [
    {"id": "hr-fetch-active-employee-salaries",
     "name": "Fetch active employee salary records",
     "description": "Retrieve all active employee salary records for a period",
     "task": "FETCH", "dom": "HR",
     "packet": "FETCH|HR|return:HR-Agent|p:1|aacp:1.1|res:emp_salary|filter:status=active|fmt:json",
     "tags": ["payroll", "salary", "employees", "monthly"],
     "version": "1.1", "source": "community", "validated": True},
    {"id": "fin-proc-invoice-three-way-match",
     "name": "Process invoice with three-way match",
     "description": "Match supplier invoice against purchase order for AP processing",
     "task": "PROC", "dom": "FIN",
     "packet": "PROC|FIN|return:FIN-Agent|p:2|aacp:1.1|res:invoice|req:po_match,gr_match|validate:three_way_match",
     "tags": ["invoice", "ap", "three-way-match", "procurement"],
     "version": "1.1", "source": "community", "validated": True},
    {"id": "it-build-ad-account",
     "name": "Create Active Directory account",
     "description": "Create new user account in Active Directory with birthright access",
     "task": "BUILD", "dom": "IT",
     "packet": "BUILD|IT|return:IT-Agent|p:1|aacp:1.1|res:ad_account|fields:email,dept,grp,pwd_reset",
     "tags": ["provisioning", "ad", "entra", "joiner"],
     "version": "1.1", "source": "community", "validated": True},
    {"id": "sales-calc-lead-score-bant",
     "name": "Score lead using BANT framework",
     "description": "Score lead against Budget Authority Need Timeline criteria",
     "task": "CALC", "dom": "SALES",
     "packet": "CALC|SALES|return:SALES-Agent|p:1|aacp:1.1|res:lead_score|rules:bant",
     "tags": ["leads", "bant", "scoring", "qualification"],
     "version": "1.1", "source": "community", "validated": True},
]

# Write temp index file
with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
    json.dump({"rules": test_rules}, f)
    tmp_path = f.name

# from_file
registry = RuleRegistry.from_file(tmp_path)
check("from_file loads rules",        len(registry) == 4)
check("repr shows count",             "4" in repr(registry))

# find
rule = registry.find("payroll salary employees")
check("find returns a rule",          rule is not None)
check("find returns correct rule",    rule.id == "hr-fetch-active-employee-salaries")
check("rule has packet",              rule.packet.startswith("FETCH|HR|"))
check("rule cost is $0.00",           rule.cost == 0.0)
check("rule encoder_type is community", rule.encoder_type == "community")

# find with domain filter
rule2 = registry.find("invoice purchase order", domain="FIN")
check("find with domain filter",      rule2 is not None)
check("domain filter works",          rule2.dom == "FIN")

# find with task filter
rule3 = registry.find("lead score", task="CALC")
check("find with task filter",        rule3 is not None)
check("task filter works",            rule3.task == "CALC")

# find_all
results = registry.find_all("account provisioning active directory")
check("find_all returns list",        isinstance(results, list))
check("find_all has results",         len(results) > 0)

# get by id
rule4 = registry.get("it-build-ad-account")
check("get by id works",              rule4 is not None)
check("get returns correct rule",     rule4.task == "BUILD")

# get missing id
missing = registry.get("nonexistent-rule")
check("get missing returns None",     missing is None)

# by_domain
hr_rules = registry.by_domain("HR")
check("by_domain filters correctly",  len(hr_rules) == 1)
check("by_domain returns HR rules",   all(r.dom == "HR" for r in hr_rules))

# by_task
fetch_rules = registry.by_task("FETCH")
check("by_task filters correctly",    len(fetch_rules) == 1)

# summary
summary = registry.summary()
check("summary returns string",       isinstance(summary, str))
check("summary shows count",          "4" in summary)

# no match returns None
no_match = registry.find("completely unrelated zebra")
check("no match returns None",        no_match is None)

# Clean up
os.unlink(tmp_path)

print(f"\n{'='*55}")
print(f"  RESULTS: {passed} passed, {failed} failed")
print(f"{'='*55}")
if failed == 0:
    print("\n  RuleRegistry ready for v1.4.\n")
else:
    sys.exit(1)
