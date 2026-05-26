"""
AACP v1.0 Rule-Based Encoder
Everything except TASK and DOM goes into named key:value extended fields.
No positional optional slots = no empty pipes.

Packet format:
  TASK|DOM|return:AGENT|p:PRIORITY|aacp:VERSION|key:value|key:value...
"""

from .base import BaseEncoder
from ..schema import (
    EncodedPacket, CompressionLoss, EncoderType, AACP_VERSION,
)
from ..validator import AACPValidator


class RuleBasedEncoder(BaseEncoder):

    def __init__(self):
        self.validator = AACPValidator()

    def encode(self,
        task: str, domain: str, return_agent: str,
        res: str = None, period: str = None,
        filter_expr: str = None, fields: list = None,
        fmt: str = None, priority: str = "2",
        src: list = None, src_prev: str = None,
        rules: str = None, validate: str = None,
        template: str = None, data_ptr: str = None,
        amt: str = None, ccy: str = None,
        supplier: str = None, match: str = None,
        terms: str = None, doc_type: str = None,
        party: str = None, clause: str = None,
        issue: str = None, risk: str = None,
        block: str = None, flags: list = None,
        flags_inherit: list = None, req: list = None,
        highlight: str = None, status: str = None,
        to: list = None, subj: str = None,
        att: str = None, flag_msg: str = None,
        tone: str = None, sentiment: str = None,
        actor: str = None, chain: list = None,
        prog: float = None, **kwargs,
    ) -> EncodedPacket:

        # Core: TASK and DOM positional, everything else named
        parts = [task.upper(), domain.upper(),
                 f"return:{return_agent}", f"p:{priority}", f"aacp:{AACP_VERSION}"]

        def add(key, val):
            if val is not None and str(val).strip():
                parts.append(f"{key}:{val}")

        add("res",      res)
        add("period",   period)
        add("filter",   filter_expr)
        add("fields",   ",".join(fields) if fields else None)
        add("fmt",      fmt)
        add("src",      ",".join(src) if src else None)
        add("src_prev", src_prev)
        add("rules",    rules)
        add("validate", validate)
        add("tmpl",     template)
        add("data_ptr", data_ptr)
        add("amt",      str(amt) if amt else None)
        add("ccy",      ccy.upper() if ccy else None)
        add("sup",      supplier.replace(" ","-") if supplier else None)
        add("match",    match)
        add("terms",    terms)
        add("type",     doc_type.upper() if doc_type else None)
        add("party",    party.replace(" ","-") if party else None)
        add("clause",   clause)
        add("issue",    issue.replace(" ","_").lower() if issue else None)
        add("risk",     risk.lower() if risk else None)
        add("block",    block)
        add("flags",    ",".join(flags) if flags else None)
        add("flags_inherit", ",".join(flags_inherit) if flags_inherit else None)
        add("req",      ",".join(req) if req else None)
        add("highlight",highlight)
        add("status",   status)
        add("to",       ",".join(to) if to else None)
        add("subj",     subj.replace(" ","_") if subj else None)
        add("att",      att)
        add("flag_msg", flag_msg.replace(" ","_") if flag_msg else None)
        add("sentiment",sentiment.lower() if sentiment else None)
        add("tone",     tone.lower() if tone else None)
        add("prog",     f"{prog:.2f}" if prog is not None else None)
        add("actor",    actor)
        add("chain",    ",".join(chain) if chain else None)

        packet = "|".join(parts)

        validation = self.validator.validate(packet)
        if not validation.valid:
            raise ValueError(
                f"Rule-based encoder produced invalid packet:\n"
                f"{chr(10).join(validation.errors)}\n{packet}"
            )

        return EncodedPacket(
            packet=packet, domain=domain.upper(), task=task.upper(),
            token_estimate_english=self._estimate_english_tokens(len(parts)),
            token_estimate_packet=self._estimate_tokens(packet),
            compression_loss=CompressionLoss.NONE,
            loss_note=None, aacp_version=AACP_VERSION,
            encoder_type=EncoderType.RULE_BASED, api_cost_usd=0.0,
        )
