# CheckGuard: Check Cashing Risk & Verification Assistant

An agentic AI assistant designed for check-cashing business tellers and store managers to assess transaction risk, verify issuing institutions, calculate cashing fees, inspect historical records, and track business statistics.

Built with Google's **Agent Development Kit (ADK)** and deployed with **`agents-cli`** on Google Cloud Agent Platform.

<div align="center">
  <img src="assets/demo.gif" alt="CheckGuard Demo" width="85%" />
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

> [!NOTE]
> **Planned, Not Yet Implemented**: Multimodal OCR check image scanning (reading handwritten check photos directly via vision models) was planned in the project brief but is not yet implemented in the current code.

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

## 📁 Repository Structure

```
.
├── assets/
│   ├── build-with-gemini-banner.png
│   └── demo.gif                     # Real screen-capture walkthrough
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
