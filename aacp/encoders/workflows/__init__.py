"""
AACP v1.1 Workflow Encoders
Zero-cost deterministic encoding for known business workflow types.

Available encoders and their real-world basis:

PayrollEncoder      HR payroll (HMRC PAYE, UK payroll practice)
ITEncoder           IT provisioning (Microsoft Entra ID / AD)
InvoiceEncoder      AP invoice processing (purchase order matching)
ContractEncoder     Legal contract review (NDA/MSA)
SalesEncoder        Sales qualification (Salesforce Agentforce, HubSpot Breeze)
JMLEncoder          HR onboarding/offboarding (ConductorOne, Lumos, CloudEagle)
CSResolutionEncoder Customer service (Zendesk Resolution Platform)
MonthEndEncoder     Finance month-end close (NetSuite Autonomous Close, BlackLine)
"""

from .payroll         import PayrollEncoder
from .it_provisioning import ITEncoder
from .finance_legal   import InvoiceEncoder, ContractEncoder
from .sales           import SalesEncoder
from .jml             import JMLEncoder
from .customer_service import CSResolutionEncoder
from .month_end       import MonthEndEncoder

__all__ = [
    "PayrollEncoder",
    "ITEncoder",
    "InvoiceEncoder",
    "ContractEncoder",
    "SalesEncoder",
    "JMLEncoder",
    "CSResolutionEncoder",
    "MonthEndEncoder",
]
