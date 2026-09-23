# My agent: CheckGuard (Check Cashing Risk & Verification Assistant)
One-liner: A conversational agent that helps check-cashing business employees verify checks and assess cashing risk using past bearer/issuer records, OCR checks, and risk calculation.

Tool coverage:
- Memory: Remembers business-specific rules, teller preferences/risk tolerance thresholds, and repeat flagged customers/issuers across sessions.
- Tools: Check verification lookup by bearer and issuer name; check history ledger search (previous returned checks, cleared checks, fraud flags); recording new check decisions (approved, held, rejected).
- Catalog/UI: Catalog of recent check transactions, high-risk issuers/bearers, and verification result summary cards (with status badges, risk score, and breakdown).
- Image gen: Generates a clear visual confirmation card or annotated check inspection diagram highlighting risk indicators/verification badge.
- Sandbox: Computes risk score formulas, cashing fee calculations based on check amount/risk tier, and daily cashing limits compliance.

Recommended for every project: memory, storage, tools, image generation, A2UI
Agent-specific / stretch (pick what fits): Code sandbox for check cashing fee and multi-factor risk score calculation, multimodal check inspection.
