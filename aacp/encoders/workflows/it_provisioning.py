"""AACP v1.0 IT Provisioning Workflow Encoder"""
from ..rule_based import RuleBasedEncoder
from ...schema import EncodedPacket

class ITEncoder:
    def __init__(self): self._enc = RuleBasedEncoder()

    def create_ad_account(self, username: str, email: str, department: str,
                          return_agent="IT-Agent", priority="1") -> EncodedPacket:
        return self._enc.encode(
            task="BUILD", domain="IT", res="ad_account",
            filter_expr=f"usr={username}",
            fields=["email","dept","grp","pwd_reset"],
            fmt="json", return_agent=return_agent, priority=priority,
        )

    def provision_email(self, email: str, licence="m365_business_standard",
                        return_agent="IT-Agent", priority="1") -> EncodedPacket:
        return self._enc.encode(
            task="PROC", domain="IT", res="m365_mailbox",
            filter_expr=f"email={email}",
            fields=["licence","sig","dl"],
            return_agent=return_agent, priority=priority,
        )

    def provision_vpn(self, username: str, return_agent="IT-Agent", priority="2") -> EncodedPacket:
        return self._enc.encode(
            task="PROC", domain="IT", res="vpn_access",
            filter_expr=f"usr={username}",
            fields=["profile","mfa"],
            return_agent=return_agent, priority=priority,
        )

    def provision_crm(self, username: str, profile="sales_rep",
                      team=None, return_agent="IT-Agent", priority="2") -> EncodedPacket:
        return self._enc.encode(
            task="PROC", domain="IT", res="salesforce_user",
            filter_expr=f"usr={username}",
            fields=["profile","team","mgr","view"],
            return_agent=return_agent, priority=priority,
        )

    def provision_badge(self, username: str, zones=None,
                        return_agent="IT-Agent", priority="2") -> EncodedPacket:
        return self._enc.encode(
            task="PROC", domain="IT", res="badge_access",
            filter_expr=f"usr={username}",
            fields=zones or ["main_entrance","office_floor"],
            return_agent=return_agent, priority=priority,
        )

    def log_provisioning(self, username: str, systems=None,
                         actor="IT-Agent", return_agent="AUD-Agent", priority="3") -> EncodedPacket:
        return self._enc.encode(
            task="LOG", domain="IT",
            filter_expr=f"usr={username}",
            chain=systems or ["AD","M365","VPN","CRM","BADGE"],
            actor=actor, status="ok",
            return_agent=return_agent, priority=priority,
        )

    def full_onboarding(self, username: str, email: str, department: str):
        return [
            self.create_ad_account(username, email, department),
            self.provision_email(email),
            self.provision_vpn(username),
            self.provision_crm(username),
            self.provision_badge(username),
            self.log_provisioning(username),
        ]
