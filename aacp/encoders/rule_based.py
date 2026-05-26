"""
AACP v1.0 Rule-Based Encoder
Deterministic pipe-delimited packet encoding. Zero LLM calls. Zero cost.
"""

from .base import BaseEncoder
from ..schema import (
    EncodedPacket, CompressionLoss, EncoderType,
    AACP_VERSION, VALID_TASKS, VALID_DOMAINS,
)
from ..validator import AACPValidator


class RuleBasedEncoder(BaseEncoder):
    """
    Encodes structured kwargs to an AACP v1.0 pipe-delimited packet.
    Zero LLM calls. Zero API cost. Deterministic output.

    Usage:
        enc = RuleBasedEncoder()
        pkt = enc.encode(
            task="FETCH", domain="HR",
            res="emp_salary", period="2024-08",
            filter_expr="status=active",
            fields=["id","dept","cc","base_sal"],
            fmt="json", return_agent="HR-Agent", priority="1",
        )
        print(pkt.packet)
        # FETCH|HR|res:emp_salary|period:2024-08|filter:status=active|
        #   fields:id,dept,cc,base_sal|fmt:json|return:HR-Agent|p:1|aacp:1.0
    """

    def __init__(self):
        self.validator = AACPValidator()

    def encode(self,
        task: str,
        domain: str,
        return_agent: str,
        res: str = None,
        period: str = None,
        filter_expr: str = None,
        fields: list = None,
        fmt: str = None,
        priority: str = "2",
        # Extended fields
        src: list = None,
        src_prev: str = None,
        rules: str = None,
        validate: str = None,
        template: str = None,
        data_ptr: str = None,
        amt: str = None,
        ccy: str = None,
        supplier: str = None,
        match: str = None,
        terms: str = None,
        doc_type: str = None,
        party: str = None,
        clause: str = None,
        issue: str = None,
        risk: str = None,
        block: str = None,
        flags: list = None,
        flags_inherit: list = None,
        req: list = None,
        highlight: str = None,
        status: str = None,
        to: list = None,
        subj: str = None,
        att: str = None,
        flag_msg: str = None,
        tone: str = None,
        sentiment: str = None,
        actor: str = None,
        chain: list = None,
        prog: float = None,
        **kwargs,
    ) -> EncodedPacket:

        # ── Positional fields (0-9) ────────────────────────────────────────────
        positional = [
            task.upper(),
            domain.upper(),
            f"res:{res}"           if res           else "",
            f"period:{period}"     if period        else "",
            f"filter:{filter_expr}" if filter_expr  else "",
            f"fields:{','.join(fields)}" if fields  else "",
            f"fmt:{fmt}"           if fmt           else "",
            f"return:{return_agent}",
            f"p:{priority}",
            f"aacp:{AACP_VERSION}",
        ]

        # ── Extended fields ────────────────────────────────────────────────────
        extended = {}
        if src:            extended["src"]        = ",".join(src)
        if src_prev:       extended["src_prev"]   = src_prev
        if rules:          extended["rules"]      = rules
        if validate:       extended["validate"]   = validate
        if template:       extended["tmpl"]       = template
        if data_ptr:       extended["data_ptr"]   = data_ptr
        if amt:            extended["amt"]        = str(amt)
        if ccy:            extended["ccy"]        = ccy.upper()
        if supplier:       extended["sup"]        = supplier.replace(" ", "-")
        if match:          extended["match"]      = match
        if terms:          extended["terms"]      = terms
        if doc_type:       extended["type"]       = doc_type.upper()
        if party:          extended["party"]      = party.replace(" ", "-")
        if clause:         extended["clause"]     = clause
        if issue:          extended["issue"]      = issue.replace(" ", "_").lower()
        if risk:           extended["risk"]       = risk.lower()
        if block:          extended["block"]      = block
        if flags:          extended["flags"]      = ",".join(flags)
        if flags_inherit:  extended["flags_inherit"] = ",".join(flags_inherit)
        if req:            extended["req"]        = ",".join(req)
        if highlight:      extended["highlight"]  = highlight
        if status:         extended["status"]     = status
        if to:             extended["to"]         = ",".join(to)
        if subj:           extended["subj"]       = subj.replace(" ", "_")
        if att:            extended["att"]        = att
        if flag_msg:       extended["flag_msg"]   = flag_msg.replace(" ", "_")
        if sentiment:      extended["sentiment"]  = sentiment.lower()
        if tone:           extended["tone"]       = tone.lower()
        if prog is not None: extended["prog"]     = f"{prog:.2f}"
        if actor:          extended["actor"]      = actor
        if chain:          extended["chain"]      = ",".join(chain)

        packet = self._build_packet(positional, extended)

        # Validate
        validation = self.validator.validate(packet)
        if not validation.valid:
            raise ValueError(
                f"Rule-based encoder produced invalid packet:\n"
                f"{chr(10).join(validation.errors)}\n{packet}"
            )

        english_est   = self._estimate_english_tokens(len(positional) + len(extended))
        packet_tokens = self._estimate_tokens(packet)

        return EncodedPacket(
            packet=packet,
            domain=domain.upper(),
            task=task.upper(),
            token_estimate_english=english_est,
            token_estimate_packet=packet_tokens,
            compression_loss=CompressionLoss.NONE,
            loss_note=None,
            aacp_version=AACP_VERSION,
            encoder_type=EncoderType.RULE_BASED,
            api_cost_usd=0.0,
        )
