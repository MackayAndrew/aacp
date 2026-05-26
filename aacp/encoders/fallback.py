"""
AACP v1.0 Fallback Encoder
Routes to rule-based encoder first, LLM if needed, logs every fallback.
"""

import os, json, hashlib
from datetime import datetime, timezone
from pathlib import Path
from .base import BaseEncoder
from .rule_based import RuleBasedEncoder
from ..schema import EncodedPacket


class PatternMatcher:
    PATTERNS = [
        {"id":"hr_fetch_employees",  "keywords":["employee","salary","retrieve","records"],     "domain":"HR",    "task":"FETCH"},
        {"id":"fin_fetch_budgets",   "keywords":["budget","cost centre","allocation","ytd"],     "domain":"FIN",   "task":"FETCH"},
        {"id":"fin_invoice",         "keywords":["invoice","supplier","payment","purchase"],     "domain":"FIN",   "task":"PROC"},
        {"id":"legal_review",        "keywords":["nda","contract","review","clause","legal"],    "domain":"LEGAL", "task":"FLAG"},
        {"id":"it_provision",        "keywords":["provision","access","account","directory"],    "domain":"IT",    "task":"BUILD"},
        {"id":"cs_complaint",        "keywords":["complaint","customer","upset","resolve"],      "domain":"CS",    "task":"RESOLVE"},
    ]

    def match(self, english: str, domain: str = None) -> dict:
        text = english.lower()
        best, best_score = None, 0
        for p in self.PATTERNS:
            if domain and p["domain"] != domain.upper(): continue
            hits  = sum(1 for kw in p["keywords"] if kw in text)
            score = hits / len(p["keywords"])
            if score >= 0.4 and hits >= 2 and score > best_score:
                best_score = score
                best = {**p, "score": round(score, 3)}
        return best if best_score >= 0.5 else None


class RegistryLogger:
    def __init__(self, registry_dir: str = "registry"):
        self.path = Path(registry_dir) / "unknown_patterns.json"
        Path(registry_dir).mkdir(exist_ok=True)

    def log(self, english: str, domain: str, packet: str,
            compression_loss: str, loss_note, eng_tokens: int, pkt_tokens: int) -> str:
        normalised = " ".join(english.lower().split())
        h = hashlib.sha256(normalised.encode()).hexdigest()[:12]
        entry = {
            "id": h, "timestamp": datetime.now(timezone.utc).isoformat(),
            "domain": domain.upper(), "english": english,
            "aacp_packet": packet, "compression_loss": compression_loss,
            "loss_note": loss_note, "token_estimate_english": eng_tokens,
            "token_estimate_packet": pkt_tokens,
            "reduction_pct": round((1 - pkt_tokens / max(1, eng_tokens)) * 100, 1),
            "rule_based_written": False,
        }
        existing = []
        if self.path.exists():
            try:
                with open(self.path) as f: existing = json.load(f)
            except Exception: existing = []
        if h not in {e["id"] for e in existing}:
            existing.append(entry)
            with open(self.path, "w") as f: json.dump(existing, f, indent=2)
            print(f"  [REGISTRY] Logged: {h} (domain:{domain}, loss:{compression_loss})")
        return h

    def summary(self) -> dict:
        if not self.path.exists(): return {"total":0,"by_domain":{},"pending":0}
        with open(self.path) as f: entries = json.load(f)
        by_domain = {}
        pending = 0
        for e in entries:
            d = e.get("domain","?")
            by_domain[d] = by_domain.get(d, 0) + 1
            if not e.get("rule_based_written"): pending += 1
        return {"total":len(entries),"by_domain":by_domain,"pending":pending}


class FallbackEncoder(BaseEncoder):
    """
    Routes to RuleBasedEncoder for structured input,
    LLM for English input. Logs every LLM call to registry.
    """

    def __init__(self, api_key=None, model="claude-sonnet-4-5",
                 registry_dir="registry", log_fallbacks=True):
        self.rule_enc    = RuleBasedEncoder()
        self.matcher     = PatternMatcher()
        self.logger      = RegistryLogger(registry_dir) if log_fallbacks else None
        self.log_fallbacks = log_fallbacks
        self._api_key    = api_key
        self._model      = model
        self._llm        = None

    def _get_llm(self):
        if self._llm is None:
            from .llm import LLMEncoder
            self._llm = LLMEncoder(api_key=self._api_key, model=self._model)
        return self._llm

    def encode(self, **kwargs) -> EncodedPacket:
        return self.rule_enc.encode(**kwargs)

    def encode_english(self, english: str, domain: str,
                       return_agent: str, priority: str = "2") -> EncodedPacket:
        match = self.matcher.match(english, domain)
        route = "pattern_match" if match else "llm_fallback"
        print(f"  [ROUTER] {route}" + (f" ({match['id']})" if match else "") + " — LLM call")

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
        if not self.logger: return
        s = self.logger.summary()
        print(f"\nREGISTRY: {s['total']} patterns | {s['pending']} pending rule-based")
        for d, n in sorted(s["by_domain"].items()):
            print(f"  {d}: {n}")
