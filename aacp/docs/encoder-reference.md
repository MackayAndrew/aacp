# AACP Encoder Reference

Every workflow encoder in the AACP SDK is grounded in a
documented real-world process. This document records the
basis for each encoder's workflow hops.

---

## PayrollEncoder — HR | 6 hops

**Real-world basis:** UK PAYE payroll, HMRC RTI submission requirements.

1. `FETCH|HR` — Retrieve active employee salary records
2. `FETCH|FIN` — Retrieve cost centre budget allocations
3. `MERGE|HR` — Calculate net pay, PAYE, pension, validate budgets
4. `REPORT|HR` — Generate payroll report (PDF + Excel)
5. `LOG|HR` — Write run to audit trail
6. `SEND|HR` — Distribute report to Finance Director and HR Director

---

## ITEncoder — IT | 5 hops

**Real-world basis:** Microsoft Entra ID (Azure AD) provisioning workflow.

1. `BUILD|IT` — Create Active Directory account
2. `PROC|IT` — Assign application licences
3. `BUILD|IT` — Configure access profile
4. `SEND|HR` — Send welcome email
5. `LOG|IT` — Write provisioning record to audit trail

---

## InvoiceEncoder — FIN | 3 hops

**Real-world basis:** Standard AP invoice processing, purchase order three-way match.

1. `PROC|FIN` — Process invoice, match against PO
2. `PROC|FIN` — Approve payment
3. `LOG|FIN` — Write invoice record to audit trail

---

## ContractEncoder — LEGAL | 2-3 hops

**Real-world basis:** Enterprise NDA and MSA review process.

1. `FLAG|LEGAL` — Review contract against template rules
2. `FLAG|LEGAL` — Flag specific clauses (risk-rated)
3. `LOG|LEGAL` — Write review record to audit trail

---

## SalesEncoder — SALES | 5 hops

**Real-world basis:**
Salesforce Agentforce 2026 CRM Automation Guide (Digital Applied, Feb 2026).
HubSpot State of Marketing Report 2025.
Salesforce Agentforce: autonomous lead qualification and rep notification.

1. `FETCH|SALES` — Fetch lead profile and engagement history
2. `CALC|SALES` — Score lead against BANT/MEDDIC framework
3. `PROC|SALES` — Route to rep or nurture sequence
4. `LOG|SALES` — Write qualification outcome to CRM audit trail
5. `SEND|SALES` — Notify assigned rep

---

## JMLEncoder — HR + IT | 6 hops (joiner), 1 (mover), 2 (leaver)

**Real-world basis:**
JML Best Practices for IT Teams 2025 (CloudEagle, Oct 2025) —
automating JML reduces identity security incidents by 67%.
8-Step IAM Implementation Plan (ConductorOne, March 2026).
Perfecting the JML Process with Entra ID (Kocho, May 2026).

**Joiner:**
1. `FETCH|HR` — Fetch new hire record
2. `BUILD|IT` — Create Active Directory / Entra ID account
3. `PROC|IT` — Assign role-based licences
4. `BUILD|IT` — Configure system access profile
5. `SEND|HR` — Send welcome email
6. `LOG|IT` — Write provisioning record to audit trail

**Mover:** `PROC|IT` — Update access for role change (revoke old, grant new)

**Leaver:** `PROC|IT` revoke all access + `LOG|IT` offboarding record

---

## CSResolutionEncoder — CS | 5 hops

**Real-world basis:**
Zendesk Autonomous Service Workforce at Relate 2026 (CMSWire, May 2026) —
Voice AI Agents resolving 80% of tickets without human intervention.
Zendesk Resolution Platform (April 2026).
ServiceNow Autonomous CRM — 100M+ cases monthly (May 2026).

1. `FETCH|CS` — Fetch customer profile, LTV, loyalty, open tickets
2. `PROC|CS` — Triage complaint by intent, sentiment, and priority
3. `RESOLVE|CS` — Route resolution with tone and goodwill guidance
4. `SEND|CS` — Send resolution response to customer
5. `LOG|CS` — Write resolution outcome to audit trail

---

## MonthEndEncoder — FIN | 6 hops

**Real-world basis:**
NetSuite 2026.1 Autonomous Close (Oracle, March 2026).
AI Agent Orchestration Reduces Month-End Close Time (Peakflo, May 2026) —
bank recon 4-8 hours to 15-30 min; accruals 6-12 hours to 30-60 min.
BlackLine Smart Close — automated reconciliation within SAP/Oracle (2025).

1. `FETCH|FIN` — Fetch trial balance and open items from GL
2. `PROC|FIN` — Run bank reconciliation against GL
3. `CALC|FIN` — Calculate accruals and post journal entries
4. `CALC|FIN` — Run variance analysis vs prior period and budget
5. `REPORT|FIN` — Generate management accounts pack
6. `LOG|FIN` — Write close certification to audit trail

---

## Summary

| Encoder | Domain | Hops | Primary citation |
|---|---|---|---|
| PayrollEncoder | HR | 6 | HMRC PAYE |
| ITEncoder | IT | 5 | Microsoft Entra ID |
| InvoiceEncoder | FIN | 3 | AP three-way match |
| ContractEncoder | LEGAL | 2-3 | NDA/MSA review |
| SalesEncoder | SALES | 5 | Salesforce Agentforce 2026 |
| JMLEncoder | HR+IT | 6/1/2 | ConductorOne, Lumos, CloudEagle |
| CSResolutionEncoder | CS | 5 | Zendesk Resolution Platform 2026 |
| MonthEndEncoder | FIN | 6 | NetSuite Autonomous Close 2026 |
