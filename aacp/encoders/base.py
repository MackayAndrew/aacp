"""AACP v1.0 Base Encoder"""
from abc import ABC, abstractmethod
from ..schema import AACP_VERSION


class BaseEncoder(ABC):

    @abstractmethod
    def encode(self, **kwargs):
        pass

    def _build_packet(self, positional: list, extended: dict) -> str:
        """
        Build a compact pipe-delimited AACP v1.0 packet.
        Drops empty optional fields to minimise token count.
        Always includes: TASK, DOM, return, p, aacp.
        """
        while len(positional) < 10:
            positional.append("")

        task = str(positional[0])   # pos 0 required
        dom  = str(positional[1])   # pos 1 required
        opts = [str(v) for v in positional[2:7]]  # res,period,filter,fields,fmt — optional
        ret  = str(positional[7])   # required
        p    = str(positional[8])   # required
        aacp = str(positional[9])   # required

        # Only include optional fields up to the last non-empty one
        last = -1
        for i, v in enumerate(opts):
            if v.strip():
                last = i

        if last >= 0:
            core = [task, dom] + opts[:last+1] + [ret, p, aacp]
        else:
            core = [task, dom, ret, p, aacp]

        for k, v in extended.items():
            if v is not None and str(v).strip():
                core.append(f"{k}:{v}")

        return "|".join(core)

    def _estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)

    def _estimate_english_tokens(self, n_fields: int) -> int:
        return 15 + (n_fields * 8)
