"""
AACP v1.1 HR Onboarding / JML Workflow Encoder
Zero-cost deterministic encoding for Joiner-Mover-Leaver workflows.

Real-world basis:
  Joiner-Mover-Leaver Best Practices for IT Teams 2025 (CloudEagle, Oct 2025)
  8-Step IAM Implementation Plan (ConductorOne, March 2026)
  Perfecting the JML Process with Entra ID (Kocho, May 2026)
  Lumos Identity Lifecycle Management (Lumos, Dec 2025)

Standard Joiner workflow:
  Fetch new hire → Create AD account → Assign licences →
  Configure access → Send welcome → Log audit record
"""

from ..rule_based import RuleBasedEncoder
from ...schema import EncodedPacket


class JMLEncoder:

    def __init__(self):
        self._enc = RuleBasedEncoder()

    # ── Joiner (new hire) ──────────────────────────────────────────────────────

    def fetch_new_hire(
        self,
        employee_id: str,
        return_agent: str = "HR-Agent",
        priority: str = "1",
    ) -> EncodedPacket:
        """Fetch new hire record from HR system (trigger: start date reached)."""
        return self._enc.encode(
            task="FETCH", domain="HR",
            res="employee_record",
            filter_expr=f"id={employee_id}",
            fmt="json",
            return_agent=return_agent, priority=priority,
        )

    def create_account(
        self,
        username: str,
        dept: str,
        return_agent: str = "IT-Agent",
        priority: str = "1",
    ) -> EncodedPacket:
        """Create Active Directory / Entra ID account with birthright access."""
        return self._enc.encode(
            task="BUILD", domain="IT",
            res="ad_account",
            filter_expr=f"usr={username}",
            fields=["email", "dept", "grp", "pwd_reset"],
            return_agent=return_agent, priority=priority,
        )

    def assign_licences(
        self,
        username: str,
        licences: list = None,
        return_agent: str = "IT-Agent",
        priority: str = "1",
    ) -> EncodedPacket:
        """Assign role-based application licences (M365, Slack, etc.)."""
        return self._enc.encode(
            task="PROC", domain="IT",
            res="licence_assignment",
            filter_expr=f"usr={username}",
            req=licences or ["M365", "Slack", "VPN"],
            return_agent=return_agent, priority=priority,
        )

    def configure_access(
        self,
        username: str,
        systems: list = None,
        return_agent: str = "IT-Agent",
        priority: str = "1",
    ) -> EncodedPacket:
        """Configure system access profile based on role and department."""
        return self._enc.encode(
            task="BUILD", domain="IT",
            res="access_profile",
            filter_expr=f"usr={username}",
            req=systems or ["email", "vpn", "sharepoint"],
            return_agent=return_agent, priority=priority,
        )

    def send_welcome(
        self,
        username: str,
        return_agent: str = "HR-Agent",
        priority: str = "2",
    ) -> EncodedPacket:
        """Send welcome email with credentials and onboarding instructions."""
        return self._enc.encode(
            task="SEND", domain="HR",
            to=[username],
            subj=f"welcome_{username}_onboarding",
            flag_msg="onboarding_complete",
            return_agent=return_agent, priority=priority,
        )

    def log_provisioning(
        self,
        username: str,
        actor: str = "IT-Agent",
        status: str = "provisioned",
        return_agent: str = "AUD-Agent",
        priority: str = "2",
    ) -> EncodedPacket:
        """Write provisioning record to audit trail (compliance requirement)."""
        return self._enc.encode(
            task="LOG", domain="IT",
            actor=actor,
            status=status,
            filter_expr=f"usr={username}",
            chain=["HR-Agent", "IT-Agent", "IT-Agent", "IT-Agent", "HR-Agent"],
            return_agent=return_agent, priority=priority,
        )

    def full_joiner(
        self,
        employee_id: str,
        username: str,
        dept: str,
        licences: list = None,
    ) -> list:
        """Full 6-hop JML joiner workflow."""
        return [
            self.fetch_new_hire(employee_id),
            self.create_account(username, dept),
            self.assign_licences(username, licences),
            self.configure_access(username),
            self.send_welcome(username),
            self.log_provisioning(username),
        ]

    # ── Mover (role change) ───────────────────────────────────────────────────

    def update_access(
        self,
        username: str,
        new_role: str,
        return_agent: str = "IT-Agent",
        priority: str = "1",
    ) -> EncodedPacket:
        """Update access permissions for role change — revoke old, grant new."""
        return self._enc.encode(
            task="PROC", domain="IT",
            res="access_update",
            filter_expr=f"usr={username}",
            rules=f"role={new_role}",
            validate="no_privilege_creep",
            return_agent=return_agent, priority=priority,
        )

    # ── Leaver (offboarding) ──────────────────────────────────────────────────

    def revoke_access(
        self,
        username: str,
        return_agent: str = "IT-Agent",
        priority: str = "1",
    ) -> EncodedPacket:
        """Immediately revoke all access on termination."""
        return self._enc.encode(
            task="PROC", domain="IT",
            res="access_revocation",
            filter_expr=f"usr={username}",
            req=["disable_ad", "revoke_licences", "revoke_vpn"],
            return_agent=return_agent, priority=priority,
        )

    def log_offboarding(
        self,
        username: str,
        actor: str = "IT-Agent",
        return_agent: str = "AUD-Agent",
        priority: str = "1",
    ) -> EncodedPacket:
        """Write offboarding record to audit trail (security compliance)."""
        return self._enc.encode(
            task="LOG", domain="IT",
            actor=actor,
            status="offboarded",
            filter_expr=f"usr={username}",
            return_agent=return_agent, priority=priority,
        )
