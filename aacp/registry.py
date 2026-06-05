"""
AACP RuleRegistry
Loads community rules for zero-cost coordination encoding.

Usage:
    from aacp import RuleRegistry

    # Load 241 community rules locally from GitHub
    registry = RuleRegistry.from_community()

    # Load from hosted registry API
    registry = RuleRegistry.from_hosted()

    # Search for a matching rule
    rule = registry.find("payroll fetch employees")
    if rule:
        print(rule.packet)  # FETCH|HR|return:HR-Agent|p:1|aacp:1.1|...
        print(rule.cost)    # 0.0

    # Use with FallbackEncoder as Tier 0
    from aacp.encoders.fallback import FallbackEncoder
    encoder = FallbackEncoder(registry=registry)
    pkt = encoder.encode_english("fetch active employee salaries", domain="HR")
"""

import json
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

COMMUNITY_RULES_URL = (
    "https://raw.githubusercontent.com/MackayAndrew/"
    "aacp-community-rules/main/index.json"
)

HOSTED_REGISTRY_URL = "https://registry.aacp.dev/rules"


@dataclass
class Rule:
    """A single validated AACP coordination rule."""
    id:          str
    name:        str
    description: str
    task:        str
    dom:         str
    packet:      str
    tags:        list
    version:     str
    source:      str
    validated:   bool

    @property
    def cost(self) -> float:
        return 0.0

    @property
    def encoder_type(self) -> str:
        return "community"

    def __repr__(self):
        return f"Rule(id={self.id!r}, packet={self.packet!r})"


class RuleRegistry:
    """
    Pre-loaded registry of validated AACP coordination rules.
    Provides zero-cost encoding for known workflow patterns.

    Acts as Tier 0 in the FallbackEncoder chain:
      Tier 0: Community registry match  → $0.00
      Tier 1: Hash cache match          → $0.00
      Tier 2: Pattern match             → $0.00
      Tier 3: LLM fallback              → ~$0.002 (once, then cached)
    """

    def __init__(self, rules: list):
        self._rules = [Rule(**r) if isinstance(r, dict) else r for r in rules]
        self._by_id = {r.id: r for r in self._rules}

    def __len__(self):
        return len(self._rules)

    def __repr__(self):
        return f"RuleRegistry({len(self._rules)} rules)"

    # ── Class methods ──────────────────────────────────────────────────────

    @classmethod
    def from_community(cls, cache: bool = True) -> "RuleRegistry":
        """
        Load 241 community rules from GitHub.
        Caches locally after first download.

        Args:
            cache: If True, cache rules locally for offline use.
        """
        cache_path = Path.home() / ".aacp" / "community_rules.json"

        if cache and cache_path.exists():
            with open(cache_path) as f:
                data = json.load(f)
            rules = data if isinstance(data, list) else data.get("rules", [])
            return cls(rules)

        try:
            with urllib.request.urlopen(COMMUNITY_RULES_URL, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            rules = data if isinstance(data, list) else data.get("rules", [])

            if cache:
                cache_path.parent.mkdir(exist_ok=True)
                with open(cache_path, "w") as f:
                    json.dump(rules, f)

            return cls(rules)

        except Exception as e:
            raise RuntimeError(
                f"Failed to load community rules from GitHub: {e}\n"
                f"Check your internet connection or use RuleRegistry.from_file()."
            )

    @classmethod
    def from_hosted(cls, url: str = HOSTED_REGISTRY_URL,
                    domain: str = None) -> "RuleRegistry":
        """
        Load rules from the hosted registry API at registry.aacp.dev.

        Args:
            url:    Registry API base URL.
            domain: Optional domain filter (HR, FIN, IT, etc.)
        """
        endpoint = url
        if domain:
            endpoint += f"?domain={domain.upper()}&limit=250"
        else:
            endpoint += "?limit=250"

        try:
            with urllib.request.urlopen(endpoint, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            rules = data.get("rules", [])
            return cls(rules)

        except Exception as e:
            raise RuntimeError(
                f"Failed to load rules from {endpoint}: {e}\n"
                f"Check registry.aacp.dev is reachable."
            )

    @classmethod
    def from_file(cls, path: str) -> "RuleRegistry":
        """Load rules from a local JSON file (index.json or rules array)."""
        with open(path) as f:
            data = json.load(f)
        rules = data if isinstance(data, list) else data.get("rules", [])
        return cls(rules)

    # ── Search ─────────────────────────────────────────────────────────────

    def find(
        self,
        query:  str,
        domain: str = None,
        task:   str = None,
    ) -> Optional[Rule]:
        """
        Find the best matching rule for a natural language query.
        Returns the highest-scoring match or None.

        Args:
            query:  Natural language description of the coordination task.
            domain: Optional domain filter (HR, FIN, IT, SALES, CS, LEGAL, MKT).
            task:   Optional task filter (FETCH, PROC, MERGE, etc.).
        """
        candidates = self._rules

        if domain:
            candidates = [r for r in candidates if r.dom == domain.upper()]
        if task:
            candidates = [r for r in candidates if r.task == task.upper()]

        if not candidates:
            return None

        words = set(re.sub(r"[^a-z0-9 ]", " ", query.lower()).split())
        scored = []

        for rule in candidates:
            tag_words  = set(t.lower() for t in rule.tags)
            name_words = set(rule.name.lower().split())
            desc_words = set(rule.description.lower().split())
            pool       = tag_words | name_words | desc_words
            score      = len(words & pool)
            if score > 0:
                scored.append((score, rule))

        if not scored:
            return None

        scored.sort(key=lambda x: -x[0])
        return scored[0][1]

    def find_all(
        self,
        query:  str,
        domain: str = None,
        task:   str = None,
        limit:  int = 5,
    ) -> list:
        """Return top N matching rules for a query."""
        candidates = self._rules
        if domain:
            candidates = [r for r in candidates if r.dom == domain.upper()]
        if task:
            candidates = [r for r in candidates if r.task == task.upper()]

        words  = set(re.sub(r"[^a-z0-9 ]", " ", query.lower()).split())
        scored = []
        for rule in candidates:
            pool  = (set(t.lower() for t in rule.tags)
                     | set(rule.name.lower().split())
                     | set(rule.description.lower().split()))
            score = len(words & pool)
            if score > 0:
                scored.append((score, rule))

        scored.sort(key=lambda x: -x[0])
        return [r for _, r in scored[:limit]]

    def get(self, rule_id: str) -> Optional[Rule]:
        """Get a rule by exact id."""
        return self._by_id.get(rule_id)

    def by_domain(self, domain: str) -> list:
        """Get all rules for a domain."""
        return [r for r in self._rules if r.dom == domain.upper()]

    def by_task(self, task: str) -> list:
        """Get all rules for a task type."""
        return [r for r in self._rules if r.task == task.upper()]

    def summary(self) -> str:
        """Print a summary of the registry contents."""
        from collections import Counter
        by_domain = Counter(r.dom  for r in self._rules)
        by_task   = Counter(r.task for r in self._rules)
        lines = [
            f"RuleRegistry: {len(self._rules)} rules",
            "By domain: " + ", ".join(f"{d}:{n}" for d, n in sorted(by_domain.items())),
            "By task:   " + ", ".join(f"{t}:{n}" for t, n in sorted(by_task.items())),
        ]
        return "\n".join(lines)
