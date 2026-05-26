"""
AACP v1.0 — Agent Action Compression Protocol
Pipe-delimited coordination protocol for multi-agent LLM systems.

Measured token reduction: ~22% vs English (live API, Claude + GPT-4o)
Rule-based encoder cost:  $0.00 for known workflows
Format: TASK|DOM|res:RES|period:P|filter:F|fields:FL|fmt:FMT|return:AGENT|p:PRI|aacp:1.0

Quick start:
    from aacp.encoders.workflows.payroll import PayrollEncoder
    enc = PayrollEncoder()
    pkt = enc.fetch_employees("2024-08")
    print(pkt.packet)

    from aacp import AACPValidator, AACPDecoder
    v = AACPValidator()
    print(v.validate(pkt.packet).summary())
"""
from .schema import (
    CompressionLoss, EncoderType, ValidationResult,
    EncodedPacket, DecodedPacket, AACP_VERSION,
    VALID_TASKS, VALID_DOMAINS, EXTENDED_FIELDS,
)
from .validator import AACPValidator
from .decoder import AACPDecoder
from .encoders import RuleBasedEncoder, LLMEncoder, FallbackEncoder

__version__ = AACP_VERSION
__all__ = [
    "AACPValidator","AACPDecoder",
    "RuleBasedEncoder","LLMEncoder","FallbackEncoder",
    "CompressionLoss","EncoderType","ValidationResult",
    "EncodedPacket","DecodedPacket","AACP_VERSION",
    "VALID_TASKS","VALID_DOMAINS","EXTENDED_FIELDS",
]
