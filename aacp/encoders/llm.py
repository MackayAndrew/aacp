"""
AACP v1.0 LLM Encoder
Compresses English instructions to AACP v1.0 pipe-delimited packets via Claude.
Used only by FallbackEncoder for novel instructions not covered by rule-based encoders.
Every call is logged to registry/unknown_patterns.json as a rule-based candidate.
"""

import os, re, json
import anthropic
from .base import BaseEncoder
from ..schema import CompressionLoss, EncodedPacket, EncoderType, AACP_VERSION
from ..validator import AACPValidator

SYSTEM_PROMPT = f"""You are an AACP v1.0 encoder.
Convert English agent instructions to AACP v1.0 pipe-delimited packets.

AACP v1.0 format (10 positional fields, pipe-separated):
  TASK|DOM|res:RES|period:PERIOD|filter:FILTER|fields:FIELDS|fmt:FMT|return:AGENT|p:PRIORITY|aacp:1.0

Field rules:
  - Field 0: TASK — FETCH PROC FLAG RESOLVE LOG SEND BUILD MERGE CALC REPORT ACK SYNC
  - Field 1: DOM  — HR FIN SALES LEGAL IT CS MKT
  - Fields 2-6: optional, use key:value format, leave empty if not needed
  - Field 7: return:AGENT_ID (required)
  - Field 8: p:1-3 (1=critical 2=medium 3=low)
  - Field 9: aacp:1.0 (always)
  - Additional fields appended after field 9 as |key:value pairs

Be minimal — only encode information present in the input.
Use abbreviated values. Prefer data_ptr URIs over inline data.

Respond with JSON only:
{{
  "packet": "pipe-delimited packet string",
  "compression_loss": "none|minor|partial|significant",
  "loss_note": "explanation if loss not none, else null",
  "task": "TASK value",
  "domain": "DOM value",
  "token_estimate_english": integer,
  "token_estimate_packet": integer
}}"""


class LLMEncoder(BaseEncoder):

    def __init__(self, api_key=None, model="claude-sonnet-4-5"):
        self.client    = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model     = model
        self.validator = AACPValidator()

    def encode(self, english: str, domain: str, return_agent: str,
               priority: str = "2", **kwargs) -> EncodedPacket:

        user = f"Domain: {domain}\nReturn: {return_agent}\nPriority: {priority}\n\n{english}"

        response = self.client.messages.create(
            model=self.model, max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user}],
        )

        raw = response.content[0].text.strip()
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        data = json.loads(raw)

        packet = data["packet"]
        if f"return:{return_agent}" not in packet:
            packet += f"|return:{return_agent}"
        if f"p:{priority}" not in packet and "|p:" not in packet:
            packet += f"|p:{priority}"
        if "aacp:" not in packet:
            packet += f"|aacp:{AACP_VERSION}"

        validation = self.validator.validate(packet)
        if not validation.valid:
            loss = CompressionLoss.PARTIAL
            loss_note = f"Invalid packet: {'; '.join(validation.errors)}"
        else:
            loss = CompressionLoss(data["compression_loss"])
            loss_note = data.get("loss_note")

        return EncodedPacket(
            packet=packet, domain=data["domain"], task=data["task"],
            token_estimate_english=data["token_estimate_english"],
            token_estimate_packet=data["token_estimate_packet"],
            compression_loss=loss, loss_note=loss_note,
            aacp_version=AACP_VERSION,
            encoder_type=EncoderType.LLM,
            api_cost_usd=(response.usage.input_tokens + response.usage.output_tokens) / 1_000_000 * 3.00,
        )
