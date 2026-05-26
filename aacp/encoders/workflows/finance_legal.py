"""AACP v1.0 Finance and Legal Workflow Encoders"""
from ..rule_based import RuleBasedEncoder
from ...schema import EncodedPacket

class InvoiceEncoder:
    def __init__(self): self._enc = RuleBasedEncoder()

    def process_invoice(self, supplier: str, amount: float, currency: str,
                        purchase_order: str, terms="net30",
                        return_agent="FIN-Agent", priority="2") -> EncodedPacket:
        return self._enc.encode(
            task="PROC", domain="FIN", res="invoice",
            supplier=supplier, amt=str(amount), ccy=currency,
            match=purchase_order, terms=terms,
            req=["validate","schedule_pay"],
            return_agent=return_agent, priority=priority,
        )

    def schedule_payment(self, supplier: str, amount: float, currency: str,
                         terms="net30", return_agent="FIN-Agent", priority="2") -> EncodedPacket:
        return self._enc.encode(
            task="PROC", domain="FIN", res="bank_transfer",
            supplier=supplier, amt=str(amount), ccy=currency, terms=terms,
            req=["schedule","confirm"],
            return_agent=return_agent, priority=priority,
        )

    def log_invoice(self, invoice_ref: str, supplier: str, amount: float,
                    currency: str, status="ok",
                    actor="FIN-Agent", return_agent="AUD-Agent", priority="3") -> EncodedPacket:
        return self._enc.encode(
            task="LOG", domain="FIN",
            filter_expr=f"inv={invoice_ref}",
            supplier=supplier, amt=str(amount), ccy=currency,
            status=status, actor=actor,
            return_agent=return_agent, priority=priority,
        )


class ContractEncoder:
    def __init__(self): self._enc = RuleBasedEncoder()

    def request_review(self, contract_type: str, party: str,
                       risk_level="medium", return_agent="LEG-Agent", priority="1") -> EncodedPacket:
        return self._enc.encode(
            task="FLAG", domain="LEGAL",
            doc_type=contract_type, party=party, risk=risk_level,
            req=["clause_review","risk_assess","sign_recommend"],
            return_agent=return_agent, priority=priority,
        )

    def flag_clause(self, contract_type: str, party: str, clause_ref: str,
                    issue: str, risk="high", block_action="signature",
                    return_agent="LEG-Agent", priority="1") -> EncodedPacket:
        return self._enc.encode(
            task="FLAG", domain="LEGAL",
            doc_type=contract_type, party=party,
            clause=clause_ref, issue=issue,
            risk=risk, block=block_action,
            req=["senior_review"],
            return_agent=return_agent, priority=priority,
        )

    def log_review(self, contract_type: str, party: str, risk: str,
                   recommendation: str, actor="LEG-Agent",
                   return_agent="AUD-Agent", priority="2") -> EncodedPacket:
        return self._enc.encode(
            task="LOG", domain="LEGAL",
            doc_type=contract_type, party=party,
            risk=risk, status=recommendation, actor=actor,
            return_agent=return_agent, priority=priority,
        )
