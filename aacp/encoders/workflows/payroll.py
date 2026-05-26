"""AACP v1.0 Payroll Workflow Encoder — pipe-delimited, zero cost."""
from ..rule_based import RuleBasedEncoder
from ...schema import EncodedPacket

class PayrollEncoder:
    def __init__(self): self._enc = RuleBasedEncoder()

    def fetch_employees(self, period: str, return_agent="HR-Agent",
                        fields=None, priority="1") -> EncodedPacket:
        return self._enc.encode(
            task="FETCH", domain="HR", res="emp_salary", period=period,
            filter_expr="status=active", fmt="json",
            return_agent=return_agent, priority=priority,
        )

    def fetch_budgets(self, period: str, return_agent="HR-Agent", priority="1") -> EncodedPacket:
        return self._enc.encode(
            task="FETCH", domain="FIN", res="budget_cc", period=period,
            fields=["cc_id","approved_budget","ytd_spend"],
            fmt="json", return_agent=return_agent, priority=priority,
        )

    def merge_and_calculate(self, period: str, flags=None,
                            rules="payroll_v2", return_agent="HR-Agent", priority="1") -> EncodedPacket:
        return self._enc.encode(
            task="MERGE", domain="HR",
            rules=rules, validate="budget_cc",
            flags_inherit=flags or [],
            return_agent=return_agent, priority=priority,
        )

    def generate_report(self, period: str, prev_period: str,
                        return_agent="HR-Agent", priority="2") -> EncodedPacket:
        return self._enc.encode(
            task="REPORT", domain="HR",
            fmt="pdf,xlsx", highlight="REVIEW_REQ",
            return_agent=return_agent, priority=priority,
        )

    def log_run(self, period: str, actor="HR-Agent", chain=None,
                status="review_required", return_agent="AUD-Agent", priority="2") -> EncodedPacket:
        return self._enc.encode(
            task="LOG", domain="HR",
            actor=actor, chain=chain or ["HRMS","FIN","PAY","RPT"],
            status=status, return_agent=return_agent, priority=priority,
        )

    def send_report(self, period: str, to=None,
                    flag_msg="review_required", return_agent="HR-Agent", priority="2") -> EncodedPacket:
        period_label = period.replace("-","_")
        return self._enc.encode(
            task="SEND", domain="HR",
            to=to or ["fin_director","hr_director"],
            subj=f"payroll_{period_label}_REVIEW_REQ",
            att=f"rpt://payroll/{period}:pdf",
            flag_msg=flag_msg, return_agent=return_agent, priority=priority,
        )

    def full_run(self, period: str, prev_period: str, flags=None):
        return [
            self.fetch_employees(period),
            self.fetch_budgets(period),
            self.merge_and_calculate(period, flags=flags),
            self.generate_report(period, prev_period),
            self.log_run(period),
            self.send_report(period),
        ]
