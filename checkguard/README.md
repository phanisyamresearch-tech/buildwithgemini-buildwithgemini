# CheckGuard: Check Cashing Risk & Verification Assistant

An agentic AI assistant designed for check-cashing business tellers and store managers to assess transaction risk, verify issuing institutions, calculate cashing fees, inspect historical records, and track business statistics.

Built with Google's **Agent Development Kit (ADK)** and deployed with **`agents-cli`** on Google Cloud Agent Platform.

<div align="center">
  <img src="assets/demo.gif" alt="CheckGuard Demo" width="85%" />
  <p>
    📹 <b>Video Walkthroughs:</b>
    <a href="assets/antigravity_tutorial_walkthrough.mp4"><b>Watch Antigravity End-to-End Tutorial (1080p)</b></a> &nbsp;|&nbsp;
    <a href="assets/cloudrun_demo.mp4"><b>Watch Live Cloud Run Demo</b></a>
  </p>
</div>

---

## 🌟 What CheckGuard Does

CheckGuard assists tellers and managers during check-cashing transactions by executing real-time checks and business intelligence queries:

1. **FDIC Financial Institution Verification**: Queries the public FDIC BankFind API to verify that the check's issuing bank is active and FDIC-insured.
2. **Address Geocoding & Local Branch Lookup**: Uses Google Maps Geocoding and Google Places API to verify business addresses printed on checks and locate nearby branches.
3. **Historical Ledger Search**: Queries Google Cloud Firestore (`check_records`) for historical records matching the bearer (payee) or issuer (payer) to detect previous returned checks, cleared transactions, or fraud flags.
4. **Entity Risk Profiling**: Retrieves risk standing and history for both the check issuer and check bearer from Firestore (`entity_risk_profiles`).
5. **Cashing Fee & Net Payout Calculation**: Calculates statutory and store fee rates by check type (payroll, government, cashier, personal) and risk tier, flagging checks that require manager approval.
6. **Decision Recording**: Persists new check verification outcomes (approved, held, rejected) directly to Firestore.
7. **Business & Financial Statistics**: Computes store-level operational metrics—including cashed vs. rejected counts, bounce rates, total fees earned, and default losses across monthly or yearly periods.
8. **Marketing Graphic Generation**: Uses `gemini-3.1-flash-lite-image` on Vertex AI to produce branded service badges and store promo graphics, automatically uploading them to Google Cloud Storage (with strict PII/PCI security guardrails).
9. **Promotional Video Generation**: Leverages Google's Omni model (`gemini-omni-flash-preview`) to generate short motion graphics for marketing, uploaded to Google Cloud Storage.
10. **Rich Agent-First UI (A2UI)**: Renders structured transaction summaries, status cards, and fee breakdowns using A2UI cards rather than plain text.
11. **Durable Cross-Session Memory**: Stores teller preferences and operational facts across sessions via Vertex AI Memory Bank.
12. **Code Execution Sandbox**: Executes data models and fee formulas within Agent Platform's secure sandbox environment.

---

## 🔮 Future Enhancements

The following roadmap items and compliance modules are planned for subsequent iterations:

1. **Multimodal OCR Check Image Scanning**: Reading handwritten check photos directly via vision models (planned in the original project brief, not yet implemented in the current code).
2. **FinCEN Regulatory Adherences**:
   - Automated Currency Transaction Report (CTR) flagging for cash payouts exceeding statutory thresholds ($10,000+).
   - Suspicious Activity Report (SAR) indicators for structured transactions or irregular multi-check patterns.
   - Comprehensive Customer Due Diligence (CDD) and Money Services Business (MSB) recordkeeping rules.
3. **State and Local Government Regulation Compliances**:
   - Dynamic statutory fee caps conforming to specific state banking department laws (e.g., maximum percentage caps for government vs. personal checks by jurisdiction).
   - Local licensing, identification requirements, and mandatory store disclosure compliance.

---

## 🏗️ Architecture & Wired Google Cloud Services

| Capability | Implementation | Service / Model |
| --- | --- | --- |
| **Agent Reasoning Core** | ADK Agent (`checkguard/app/agent.py`) | `gemini-3.6-flash` |
| **Durable Memory** | `PreloadMemoryTool` + Session Callback | **Vertex AI Memory Bank** |
| **Database & History** | Firestore collections (`check_records`, `entity_risk_profiles`) | **Cloud Firestore** |
| **Asset Storage** | Public media bucket (`checkguard-media-*`) | **Google Cloud Storage** |
| **Marketing Images** | `generate_marketing_image` | `gemini-3.1-flash-lite-image` |
| **Marketing Videos** | `generate_promotional_video` | `gemini-omni-flash-preview` |
| **Code Execution** | `AgentEngineSandboxCodeExecutor` | **Agent Platform Sandbox** |
| **Agent UI** | A2UI schema manager + `a2ui_callback` | **A2UI v0.8** |
| **Web Frontend** | FastAPI A2A Proxy + Chat UI | **FastAPI** |
| **Bank Verification** | `verify_bank_institution` | **FDIC BankFind API** |
| **Location Verification** | `geocode_address`, `find_nearby_places` | **Google Maps & Places APIs** |

---

## 💬 Try It Out: Demo Prompts

Here are sample prompts that demonstrate each tool and capability in action:

### 1. Check Risk Assessment & History Lookup
> *"Can you check the risk on a payroll check issued by Apex Logistics to John Doe for $1,200 drawn on JPMorgan Chase?"*
- **Tools Exercised**: `verify_bank_institution` (FDIC check), `search_check_history` (Firestore ledger), `get_entity_risk_profile` (trust scores), `calculate_cashing_fee_and_payout`, and **A2UI** response card.

### 2. High-Risk / Flagged Customer Detection
> *"Sarah Connor wants to cash a $4,500 personal check issued by Cyberdyne Systems. What does our history say and what fee applies?"*
- **Tools Exercised**: `search_check_history` (uncovers returned/fraud checks), `get_entity_risk_profile`, manager override check, fee computation with risk adjustment.

### 3. Business Location & Branch Verification
> *"The check from BuildMart lists their address as 100 Industrial Pkwy, Kansas City, MO. Can you verify this location and find any nearby bank branches?"*
- **Tools Exercised**: `geocode_address` (Google Maps Geocoding) and `find_nearby_places` (Google Places API).

### 4. Record a Transaction Decision
> *"Record an approval for check #9842 presented by John Doe, issued by Apex Logistics for $1,200 with standard payroll fee."*
- **Tools Exercised**: `record_check_verification` (persists new transaction to Firestore `check_records`).

### 5. Store Manager Operations & Financial Statistics
> *"Show me our check cashing statistics for 2026. How many checks bounced, what was our total fee revenue, and what are our default losses?"*
- **Tools Exercised**: `query_business_statistics` (aggregates monthly/annual totals, bounce rates, and fee income from Firestore).

### 6. Marketing Visual Generation (Vertex AI Image Gen + GCS)
> *"Generate a promotional service graphic for our storefront window advertising instant payroll check cashing with zero waiting."*
- **Tools Exercised**: `generate_marketing_image` (`gemini-3.1-flash-lite-image`), uploads to Cloud Storage, and renders in an A2UI visual card.

### 7. Marketing Motion Graphic (Omni Video Gen + GCS)
> *"Create a 5-second dynamic motion graphic video highlighting fast, trusted check verification for our digital board."*
- **Tools Exercised**: `generate_promotional_video` (`gemini-omni-flash-preview`) and Cloud Storage asset upload.

### 8. Durable Memory (Across Sessions)
> *"Remember that our store limit for unverified first-time personal checks is strictly $500 without manager sign-off."*
- **Tools Exercised**: `generate_memories_callback` + `PreloadMemoryTool` via **Vertex AI Memory Bank**.

---

## 📁 Repository Structure

```
.
├── assets/
│   ├── antigravity_tutorial_walkthrough.mp4  # Complete end-to-end architecture & live demo tutorial
│   ├── build-with-gemini-banner.png
│   ├── cloudrun_demo.mp4            # Live recording against Cloud Run URL with prompts
│   ├── demo.gif                     # Real screen-capture walkthrough
│   ├── demo.mp4                     # Full MP4 recording
│   └── demo_lofi.mp4                # Demo with background soundtrack
├── checkguard/
│   ├── agents-cli-manifest.yaml     # Agent deployment manifest
│   ├── app/
│   │   ├── agent.py                 # Core ADK agent, tools, and callbacks
│   │   ├── a2ui_utils.py            # A2UI formatting callback
│   │   ├── firestore_tools.py       # Firestore queries and statistics calculation
│   │   └── fast_api_app.py          # FastAPI application wrapper
│   ├── frontend/
│   │   ├── main.py                  # FastAPI proxy (A2A protocol client)
│   │   └── static/index.html        # Chat interface with inline A2UI renderer
│   ├── seed_firestore.py            # Mock check records and risk profiles seeder
│   └── pyproject.toml               # Python dependencies and project metadata
└── project_brief.md                 # Original project design brief
```

---

## 🚀 Running the Project Locally

### 1. Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Google Cloud SDK (`gcloud`) authenticated to a project with Vertex AI and Firestore enabled

### 2. Environment Setup

Configure your Google Cloud project and environment variables:

```bash
gcloud auth application-default login
gcloud config set project <YOUR_PROJECT_ID>

cd checkguard
cp .env.example .env
```

Ensure `.env` contains:
```env
GOOGLE_CLOUD_PROJECT=<YOUR_PROJECT_ID>
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_MAPS_API_KEY=<YOUR_OPTIONAL_MAPS_KEY>
```

### 3. Seed Firestore Database

Initialize sample check records, past bounced transactions, and entity risk profiles:

```bash
uv run python seed_firestore.py
```

### 4. Run the Agent & Playground

You can launch the ADK development playground to interact with the agent directly:

```bash
cd checkguard
agents-cli playground
```

### 5. Run the Custom Web Frontend

To run the custom chat frontend with full A2UI card rendering:

```bash
cd checkguard/frontend
uv run python main.py
```

The web interface will start at standard local port `8080`.

---

## 📄 License

Apache License 2.0. See LICENSE for details.
