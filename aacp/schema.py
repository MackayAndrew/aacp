"""
AACP v1.0 Schema — pipe-delimited format with named fields.

Packet format:
  TASK|DOM|res:RES|period:PERIOD|filter:FILTER|fields:FIELDS|fmt:FMT|return:AGENT|p:PRIORITY|aacp:VERSION[|key:value...]

Required fields: TASK (pos 0), DOM (pos 1), return (pos 7), aacp (pos 9)
Optional positional fields: res, period, filter, fields, fmt, p
Extended fields: appended after position 9 as |key:value pairs

Example:
  FETCH|HR|res:emp_salary|period:2024-08|filter:status=active|fields:id,dept,cc,base_sal|fmt:json|return:HR-Agent|p:1|aacp:1.0
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

AACP_VERSION = "1.0"

FIELD_POSITIONS = {
    0: "TASK", 1: "DOM", 2: "res", 3: "period",
    4: "filter", 5: "fields", 6: "fmt",
    7: "return", 8: "p", 9: "aacp",
}

VALID_TASKS = {
    "FETCH","PROC","FLAG","RESOLVE","LOG","SEND",
    "BUILD","MERGE","CALC","REPORT","ACK","SYNC",
}
VALID_DOMAINS   = {"HR","FIN","SALES","LEGAL","IT","CS","MKT"}
VALID_PRIORITIES = {"1","2","3"}

EXTENDED_FIELDS = {
    "src","src_prev","rules","validate","tmpl","data_ptr",
    "amt","ccy","sup","match","terms","type","party",
    "clause","issue","risk","block","flags","req",
    "highlight","status","to","subj","att","flag_msg",
    "tone","sentiment","actor","chain","prog",
    "ltv","loyalty","urgency",
}

class CompressionLoss(Enum):
    NONE        = "none"
    MINOR       = "minor"
    PARTIAL     = "partial"
    SIGNIFICANT = "significant"

class EncoderType(Enum):
    RULE_BASED = "rule_based"
    LLM        = "llm"
    FALLBACK   = "fallback"

@dataclass
class ValidationResult:
    valid: bool
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def summary(self) -> str:
        lines = ["VALIDATION RESULT",
                 f"  Status: {'VALID' if self.valid else 'INVALID'}"]
        for e in self.errors:   lines.append(f"    ERROR: {e}")
        for w in self.warnings: lines.append(f"    WARN:  {w}")
        if not self.errors and not self.warnings:
            lines.append("  No issues.")
        return "\n".join(lines)

@dataclass
class EncodedPacket:
    packet: str
    domain: str
    task: str
    token_estimate_english: int
    token_estimate_packet: int
    compression_loss: CompressionLoss
    loss_note: Optional[str]
    aacp_version: str = AACP_VERSION
    encoder_type: EncoderType = EncoderType.RULE_BASED
    api_cost_usd: float = 0.0

    @property
    def compression_ratio(self) -> float:
        if self.token_estimate_english == 0: return 0.0
        return 1 - (self.token_estimate_packet / self.token_estimate_english)

    @property
    def reduction_pct(self) -> str:
        return f"{self.compression_ratio * 100:.1f}%"

    def summary(self) -> str:
        return "\n".join([
            f"PACKET [{self.domain}/{self.task}]",
            f"  Encoder: {self.encoder_type.value}  Cost: ${self.api_cost_usd:.4f}",
            f"  Loss:    {self.compression_loss.value}",
            "", self.packet,
        ])

@dataclass
class DecodedPacket:
    english: str
    parsed: dict
    is_complete: bool
    caveat: str = "Decoded output is structural. Packet is the canonical record."
