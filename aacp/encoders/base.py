"""AACP v1.0 Base Encoder"""
from abc import ABC, abstractmethod
from ..schema import EncodedPacket, AACP_VERSION


class BaseEncoder(ABC):

    @abstractmethod
    def encode(self, **kwargs) -> EncodedPacket:
        pass

    def _build_packet(self, positional: list, extended: dict) -> str:
        """
        Build a pipe-delimited AACP v1.0 packet.

        positional: list of 10 values for positions 0-9
                    [TASK, DOM, res:, period:, filter:, fields:, fmt:, return:, p:, aacp:]
        extended:   dict of additional key:value fields appended after position 9
        """
        # Ensure exactly 10 positional fields
        while len(positional) < 10:
            positional.append("")

        parts = [str(v) for v in positional[:10]]

        for k, v in extended.items():
            if v is not None and str(v).strip():
                parts.append(f"{k}:{v}")

        return "|".join(parts)

    def _estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)

    def _estimate_english_tokens(self, n_fields: int) -> int:
        return 15 + (n_fields * 8)
