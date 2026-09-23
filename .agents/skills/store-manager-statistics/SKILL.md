---
name: store-manager-statistics
description: >
  Query and analyze store manager business statistics on checks cashed, rejected,
  and bounced per month and per year. Use when the user asks for manager-level
  operational reports, monthly/yearly check volume, bounce rates, rejection rates,
  cashing fee revenue, default losses, or high-risk issuer breakdowns.
---

# Store Manager Business Statistics Skill

This skill teaches the agent how to retrieve, interpret, and present check cashing operational metrics, financial volumes, and loss prevention statistics for store managers and franchise supervisors.

## Overview & Key Metrics

Check-cashing operations monitor four primary categories of business statistics:

1. **Volume & Activity Metrics**:
   - **Total Presented**: Total count and dollar value of checks brought to tellers.
   - **Cashed / Cleared**: Checks approved and cashed out to customers.
   - **Rejected / Fraud Flagged**: Checks declined at the counter due to counterfeit watermarks, bad signatures, frozen accounts, or high fraud risk.
   - **Returned / Bounced**: Checks cashed by the store that were subsequently returned unpaid (NSF, stopped payment, closed account) by the paying bank.

2. **Financial Performance Metrics**:
   - **Fee Revenue**: Total cashing fees collected by the store (average 1.5%–5.0% depending on check type, or minimum $3.00/check).
   - **Average Check Amount**: Total dollar volume divided by check count.
   - **Net Bounced Loss**: Total dollar value of returned unpaid checks (direct loss to the store).

3. **Risk & Health Ratios**:
   - **Clearance Rate**: \(\frac{\text{Cashed Count}}{\text{Presented Count}} \times 100\%\) (Healthy benchmark: > 70%).
   - **Bounce Rate**: \(\frac{\text{Bounced Count}}{\text{Cashed Count} + \text{Bounced Count}} \times 100\%\) (Healthy benchmark: < 5%).
   - **Rejection Rate**: \(\frac{\text{Rejected Count}}{\text{Presented Count}} \times 100\%\) (Measures counter fraud interception).

4. **Problem Entities**:
   - Issuers or makers whose checks have bounced or triggered repeat fraud flags.

---

## Tool Execution

The agent provides the `query_business_statistics` tool to aggregate ledger data from Firestore:

```python
# Monthly query (e.g. September 2026)
stats = query_business_statistics(year=2026, month=9)

# Annual query (e.g. full year 2026)
annual_stats = query_business_statistics(year=2026)

# All-time historical summary
all_time = query_business_statistics()
```

---

## Response Formatting Guidelines for Store Managers

When answering managerial queries:

1. **Executive Summary Card / Header**:
   - Lead with the time period (e.g., September 2026 or Full Year 2026).
   - Display key counts clearly: Cashed vs. Rejected vs. Bounced.

2. **Financial Highlights**:
   - Show Total Volume Presented, Volume Successfully Cashed, and Total Fees Earned.
   - Highlight any Bounced Check Loss with an alert / notice.

3. **Key Ratios Table**:
   - Present Clearance Rate, Bounce Rate, and Rejection Rate.
   - If Bounce Rate exceeds 5%, note that teller review protocols should be tightened for high-risk issuers.

4. **Monthly Breakdown & High-Risk Issuers**:
   - For annual reviews, show a concise monthly comparison.
   - List repeat problematic issuers that tellers should be warned about.
