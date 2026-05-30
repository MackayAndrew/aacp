"""
AACP v1.1 LLM Encoder
Compresses English instructions to AACP v1.1 pipe-delimited packets via Claude.
Used only by FallbackEncoder for novel instructions not covered by rule-based encoders.
Every call is logged to registry/unknown_patterns.json as a rule-based candidate.
"""

import os, re, json
import anthropic
from .base import BaseEncoder
from ..schema import CompressionLoss, EncodedPacket, EncoderType, AACP_VERSION
from ..validator import AACPValidator

SYSTEM_PROMPT = """You are an AACP v1.1 encoder.
Convert English agent instructions to AACP v1.1 pipe-delimited packets.

AACP v1.1 format:
  TASK|DOM|return:AGENT|p:PRIORITY|aacp:1.1|key:value|key:value...

Rules:
  - Field 0: TASK — FETCH PROC FLAG RESOLVE LOG SEND BUILD MERGE CALC REPORT ACK SYNC
  - Field 1: DOM  — HR FIN SALES LEGAL IT CS MKT
  - All other fields are named key:value pairs
  - No empty positional slots
  - Required: return: and aacp:1.1
  - Optional common keys: res: period: filter: fields: fmt: rules: validate:
  - Extended keys: src: tmpl: amt: ccy: sup: match: terms: type: party:
    clause: issue: risk: block: flags: req: highlight: status: to: subj:
    tone: sentiment: actor: chain: prog:

Be minimal. Only encode information present in the input.
Do not embed field lists in packets unless explicitly required.
Do not embed URI data pointers.

Example:
  English: "Retrieve active employee salary records for August 2026, return as JSON"
  Packet: FETCH|HR|return:HR-Agent|p:1|aacp:1.1|res:emp_salary|period:2026-08|filter:status=active|fmt:json

Respond with JSON only:
{
  "packet": "pipe-delimited packet string",
  "compression_loss": "none|minor|partial|significant",
  "loss_note": "explanation if loss not none, else null",
  "task": "TASK value",
  "domain": "DOM value",
  "token_estimate_english": integer,
  "token_estimate_packet": integer
}"""


class LLMEncoder(BaseEncoder):

    def __init__(self, api_key=None, model="claude-sonnet-4-5"):
        self.client    = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model     = model
        self.validator = AACPValidator()

    def encode(self, english: str, domain: str, return_agent: str,
               priority: str = "2", **kwargs) -> EncodedPacket:

        user = (f"Domain: {domain}\n"
                f"Return agent: {return_agent}\n"
                f"Priority: {priority}\n\n"
                f"Instruction: {english}")

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

        # Ensure required fields are present
        if f"return:{return_agent}" not in packet:
            packet += f"|return:{return_agent}"
        if "|p:" not in packet and not packet.startswith("p:"):
            packet += f"|p:{priority}"
        if "aacp:" not in packet:
            packet += f"|aacp:{AACP_VERSION}"

        # Fix version tag if old format
        packet = packet.replace("|aacp:1.0", f"|aacp:{AACP_VERSION}")

        validation = self.validator.validate(packet)
        if not validation.valid:
            loss      = CompressionLoss.PARTIAL
            loss_note = f"Validation issues: {'; '.join(validation.errors)}"
        else:
            loss      = CompressionLoss(data["compression_loss"])
            loss_note = data.get("loss_note")

        tokens_in  = response.usage.input_tokens
        tokens_out = response.usage.output_tokens
        cost       = (tokens_in + tokens_out) / 1_000_000 * 3.00

        return EncodedPacket(
            packet=packet,
            domain=data.get("domain", domain).upper(),
            task=data.get("task", packet.split("|")[0]),
            token_estimate_english=data.get("token_estimate_english", 0),
            token_estimate_packet=data.get("token_estimate_packet", 0),
            compression_loss=loss,
            loss_note=loss_note,
            aacp_version=AACP_VERSION,
            encoder_type=EncoderType.LLM,
            api_cost_usd=round(cost, 6),
        )
