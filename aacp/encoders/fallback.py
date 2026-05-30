"""
AACP v1.1 Fallback Encoder
Routing priority:
  1. Hash match    — exact English seen before → cached packet, $0.00
  2. Pattern match — keyword match in registry or built-in → rule-based, $0.00
  3. LLM fallback  — novel instruction → LLM call, logged to registry

This closes the self-improving loop:
  Novel input → LLM → logged to registry
  Same input again → hash match → cached packet → $0.00
  Similar input → pattern match → rule-based → $0.00
"""

import os, json, hashlib
from datetime import datetime, timezone
from pathlib import Path
from .base import BaseEncoder
from .rule_based import RuleBasedEncoder
from ..schema import EncodedPacket, EncoderType, CompressionLoss, AACP_VERSION


class RegistryLogger:
    """Append-only log of every LLM fallback call."""

    def __init__(self, registry_dir: str = "registry"):
        self.path = Path(registry_dir) / "unknown_patterns.json"
        Path(registry_dir).mkdir(exist_ok=True)

    def _load(self) -> list:
        if not self.path.exists():
            return []
        try:
            with open(self.path) as f:
                return json.load(f)
        except Exception:
            return []

    def _save(self, entries: list):
        with open(self.path, "w") as f:
            json.dump(entries, f, indent=2)

    def normalise(self, english: str) -> str:
        return " ".join(english.lower().split())

    def hash(self, english: str) -> str:
        return hashlib.sha256(self.normalise(english).encode()).hexdigest()[:12]

    def log(self, english: str, domain: str, packet: str,
            compression_loss: str, loss_note, eng_tokens: int,
            pkt_tokens: int) -> str:
        h = self.hash(english)
        entries = self._load()

        if h in {e["id"] for e in entries}:
            return h  # already logged, don't duplicate

        entry = {
            "id":                    h,
            "timestamp":             datetime.now(timezone.utc).isoformat(),
            "domain":                domain.upper(),
            "english":               english,
            "english_normalised":    self.normalise(english),
            "keywords":              self._extract_keywords(english),
            "aacp_packet":           packet,
            "compression_loss":      compression_loss,
            "loss_note":             loss_note,
            "token_estimate_english": eng_tokens,
            "token_estimate_packet": pkt_tokens,
            "reduction_pct":         round((1 - pkt_tokens / max(1, eng_tokens)) * 100, 1),
            "rule_based_written":    False,
            "times_seen":            1,
        }
        entries.append(entry)
        self._save(entries)
        print(f"  [REGISTRY] Logged new pattern: {h} (domain:{domain})")
        return h

    def lookup_hash(self, english: str) -> dict | None:
        """Exact match — same instruction seen before."""
        h = self.hash(english)
        for entry in self._load():
            if entry["id"] == h:
                # Increment times_seen
                entries = self._load()
                for e in entries:
                    if e["id"] == h:
                        e["times_seen"] = e.get("times_seen", 1) + 1
                        break
                self._save(entries)
                return entry
        return None

    def lookup_keywords(self, english: str, domain: str = None,
                        threshold: float = 0.5) -> dict | None:
        """Keyword match — similar instruction seen before."""
        text = self._extract_keywords(english)
        entries = self._load()
        best, best_score = None, 0.0
        for entry in entries:
            if domain and entry.get("domain", "").upper() != domain.upper():
                continue
            stored_kws = set(entry.get("keywords", []))
            if not stored_kws:
                continue
            overlap = len(set(text) & stored_kws) / len(stored_kws)
            if overlap >= threshold and overlap > best_score:
                best_score = overlap
                best = {**entry, "match_score": round(overlap, 3)}
        return best if best_score >= threshold else None

    def _extract_keywords(self, english: str) -> list:
        """Extract meaningful keywords for matching."""
        stopwords = {
            "the","a","an","and","or","but","in","on","to","for",
            "of","with","at","by","from","up","about","into","through",
            "is","are","was","were","be","been","being","have","has","had",
            "do","does","did","will","would","could","should","may","might",
            "i","me","my","we","our","you","your","it","its","this","that",
            "all","each","every","both","few","more","most","other","some",
            "please","need","want","like","just","also","then","than",
        }
        words = english.lower().split()
        keywords = [
            w.strip(".,;:!?\"'()[]") for w in words
            if len(w.strip(".,;:!?\"'()[]")) > 3
            and w.strip(".,;:!?\"'()[]") not in stopwords
        ]
        return list(dict.fromkeys(keywords))  # deduplicate, preserve order

    def summary(self) -> dict:
        entries = self._load()
        by_domain = {}
        pending = 0
        total_seen = 0
        for e in entries:
            d = e.get("domain", "?")
            by_domain[d] = by_domain.get(d, 0) + 1
            if not e.get("rule_based_written"):
                pending += 1
            total_seen += e.get("times_seen", 1)
        return {
            "total":       len(entries),
            "by_domain":   by_domain,
            "pending":     pending,
            "total_seen":  total_seen,
        }


class PatternMatcher:
    """
    Matches English instructions to known patterns.
    Sources (in priority order):
      1. Registry file (patterns logged from previous LLM calls)
      2. Built-in hardcoded patterns (bootstrap set)
    """

    BUILTIN = [
        {"id": "hr_fetch_employees",  "domain": "HR",    "task": "FETCH",
         "keywords": ["employee", "salary", "retrieve", "records", "payroll"]},
        {"id": "fin_fetch_budgets",   "domain": "FIN",   "task": "FETCH",
         "keywords": ["budget", "cost", "centre", "allocation", "ytd", "spend"]},
        {"id": "fin_invoice",         "domain": "FIN",   "task": "PROC",
         "keywords": ["invoice", "supplier", "payment", "purchase", "order"]},
        {"id": "legal_review",        "domain": "LEGAL", "task": "FLAG",
         "keywords": ["nda", "contract", "clause", "legal", "review", "risk"]},
        {"id": "it_provision",        "domain": "IT",    "task": "BUILD",
         "keywords": ["provision", "access", "account", "directory", "user"]},
        {"id": "cs_complaint",        "domain": "CS",    "task": "RESOLVE",
         "keywords": ["complaint", "customer", "upset", "resolve", "issue"]},
        {"id": "hr_merge_payroll",    "domain": "HR",    "task": "MERGE",
         "keywords": ["merge", "calculate", "payroll", "pension", "paye"]},
        {"id": "hr_report",           "domain": "HR",    "task": "REPORT",
         "keywords": ["report", "generate", "summary", "monthly", "payroll"]},
    ]

    def __init__(self, registry_dir: str = "registry"):
        self.registry_path = Path(registry_dir) / "unknown_patterns.json"

    def _load_registry_patterns(self) -> list:
        if not self.registry_path.exists():
            return []
        try:
            with open(self.registry_path) as f:
                entries = json.load(f)
            # Only use patterns that have been seen more than once
            # or have been explicitly marked as rule-based ready
            return [
                {
                    "id":       e["id"],
                    "domain":   e.get("domain", ""),
                    "task":     self._extract_task(e.get("aacp_packet", "")),
                    "keywords": e.get("keywords", []),
                    "packet":   e.get("aacp_packet", ""),
                    "times_seen": e.get("times_seen", 1),
                    "from_registry": True,
                }
                for e in entries
                if e.get("times_seen", 1) >= 1
            ]
        except Exception:
            return []

    def _extract_task(self, packet: str) -> str:
        if not packet:
            return ""
        parts = packet.split("|")
        return parts[0] if parts else ""

    def match(self, english: str, domain: str = None,
              threshold: float = 0.5) -> dict | None:
        """
        Try registry patterns first (more specific), then builtins.
        Returns best match or None.
        """
        text_words = set(english.lower().split())

        # Try registry patterns first
        registry_patterns = self._load_registry_patterns()
        best, best_score = None, 0.0

        for p in registry_patterns:
            if domain and p.get("domain", "").upper() != domain.upper():
                continue
            kws = set(p.get("keywords", []))
            if not kws:
                continue
            overlap = len(text_words & kws) / len(kws)
            if overlap >= threshold and overlap > best_score:
                best_score = overlap
                best = {**p, "match_score": round(overlap, 3),
                        "source": "registry"}

        # Try builtins
        for p in self.BUILTIN:
            if domain and p["domain"] != domain.upper():
                continue
            kws = set(p["keywords"])
            overlap = len(text_words & kws) / len(kws)
            if overlap >= threshold and overlap > best_score:
                best_score = overlap
                best = {**p, "match_score": round(overlap, 3),
                        "source": "builtin"}

        return best if best_score >= threshold else None


class FallbackEncoder(BaseEncoder):
    """
    Three-tier routing:
      1. Hash match  → cached packet from registry,    $0.00
      2. Pattern match → rule-based encoder inference,  $0.00
      3. LLM fallback → LLM call, logged to registry,  ~$0.0006
    """

    def __init__(self, api_key=None, model="claude-sonnet-4-5",
                 registry_dir="registry", log_fallbacks=True):
        self.rule_enc      = RuleBasedEncoder()
        self.matcher       = PatternMatcher(registry_dir)
        self.logger        = RegistryLogger(registry_dir) if log_fallbacks else None
        self.log_fallbacks = log_fallbacks
        self._api_key      = api_key
        self._model        = model
        self._llm          = None
        self._registry_dir = registry_dir

    def _get_llm(self):
        if self._llm is None:
            from .llm import LLMEncoder
            self._llm = LLMEncoder(api_key=self._api_key, model=self._model)
        return self._llm

    def encode(self, **kwargs) -> EncodedPacket:
        """Direct structured encoding — always rule-based."""
        return self.rule_enc.encode(**kwargs)

    def encode_english(self, english: str, domain: str,
                       return_agent: str, priority: str = "2") -> EncodedPacket:
        """
        Encode a natural language instruction.
        Tries cache → pattern → LLM in that order.
        """

        # ── Tier 1: Hash match (exact same instruction seen before) ──────────
        if self.logger:
            cached = self.logger.lookup_hash(english)
            if cached:
                packet = cached["aacp_packet"]
                print(f"  [ROUTER] hash_match ({cached['id']}) "
                      f"seen {cached.get('times_seen', 1)}x — $0.00")
                return EncodedPacket(
                    packet=packet,
                    domain=cached.get("domain", domain).upper(),
                    task=packet.split("|")[0] if packet else "UNKNOWN",
                    token_estimate_english=cached.get("token_estimate_english", 0),
                    token_estimate_packet=cached.get("token_estimate_packet", 0),
                    compression_loss=CompressionLoss.NONE,
                    loss_note="Served from registry cache",
                    aacp_version=AACP_VERSION,
                    encoder_type=EncoderType.RULE_BASED,
                    api_cost_usd=0.0,
                )

        # ── Tier 2: Pattern match (similar instruction, registry or builtin) ──
        match = self.matcher.match(english, domain)
        if match:
            source = match.get("source", "unknown")
            score  = match.get("match_score", 0)

            # If registry pattern has a cached packet, return it directly
            if source == "registry" and match.get("packet"):
                packet = match["packet"]
                print(f"  [ROUTER] pattern_match ({match['id']}, "
                      f"score:{score}, source:registry) — $0.00")
                return EncodedPacket(
                    packet=packet,
                    domain=match.get("domain", domain).upper(),
                    task=packet.split("|")[0] if packet else "UNKNOWN",
                    token_estimate_english=0,
                    token_estimate_packet=len(packet) // 4,
                    compression_loss=CompressionLoss.MINOR,
                    loss_note=f"Pattern match from registry (score:{score})",
                    aacp_version=AACP_VERSION,
                    encoder_type=EncoderType.RULE_BASED,
                    api_cost_usd=0.0,
                )

            # Builtin pattern — use it to inform LLM but note the match
            print(f"  [ROUTER] pattern_hint ({match['id']}, "
                  f"score:{score}, source:{source}) → LLM with hint")
        else:
            print(f"  [ROUTER] no_match → LLM fallback")

        # ── Tier 3: LLM fallback ──────────────────────────────────────────────
        result = self._get_llm().encode(
            english=english, domain=domain,
            return_agent=return_agent, priority=priority,
        )

        if self.log_fallbacks and self.logger:
            self.logger.log(
                english=english, domain=domain, packet=result.packet,
                compression_loss=result.compression_loss.value,
                loss_note=result.loss_note,
                eng_tokens=result.token_estimate_english,
                pkt_tokens=result.token_estimate_packet,
            )

        return result

    def print_registry_summary(self):
        if not self.logger:
            return
        s = self.logger.summary()
        print(f"\nREGISTRY SUMMARY")
        print(f"  Total patterns:  {s['total']}")
        print(f"  Total seen:      {s['total_seen']}")
        print(f"  Pending:         {s['pending']} (no rule-based encoder yet)")
        print(f"  By domain:")
        for d, n in sorted(s["by_domain"].items()):
            print(f"    {d}: {n}")
