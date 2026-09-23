# Google Cloud Services & Architecture Inventory

This document provides a comprehensive inventory of all **Google Cloud services**, **Vertex AI foundation models**, **APIs**, and **runtime components** configured and utilized across the **CheckGuard** project.

Use this inventory as an architectural blueprint and reference for roadmap execution and future enhancements (e.g., FinCEN compliance, multimodal OCR, automated audits).

---

## 📋 Service Inventory Matrix

| Google Cloud Service / Component | Role / Purpose in CheckGuard | Resource Name / Configuration | Key Code Reference |
| :--- | :--- | :--- | :--- |
| **Vertex AI Agent Engine (Agent Runtime)** | Serves the core ADK agent over the standardized **A2A (Agent-to-Agent)** protocol with stateless scaling. | `projects/1069102362772/locations/us-central1/reasoningEngines/7355024154577338368` | [`checkguard/deployment_metadata.json`](file:///config/Desktop/BuildWithGemini/checkguard/deployment_metadata.json), [`checkguard/agents-cli-manifest.yaml`](file:///config/Desktop/BuildWithGemini/checkguard/agents-cli-manifest.yaml) |
| **Vertex AI Memory Bank** | Durable, cross-session long-term memory storing teller instructions, store policies, and compliance limits. | Engine URI: `agentengine://6432349180919808000` | [`checkguard/app/agent.py`](file:///config/Desktop/BuildWithGemini/checkguard/app/agent.py#L422-L445) (`PreloadMemoryTool`, `generate_memories_callback`) |
| **Vertex AI Foundation Models** | • **Reasoning & Tool Orchestration**: `gemini-3.6-flash`<br>• **Marketing Image Gen**: `gemini-3.1-flash-lite-image`<br>• **Promotional Motion Video Gen**: `gemini-omni-flash-preview` | Vertex AI Model Garden (`us-central1`) | [`checkguard/app/agent.py`](file:///config/Desktop/BuildWithGemini/checkguard/app/agent.py#L255-L420) |
| **Google Cloud Firestore (Datastore Mode / Native)** | Persistent NoSQL database storing transactional check history (`check_records`), entity trust ratings (`entities`), and ledger statistics. | Collections: `check_records`, `entities`<br>Project: `qwiklabs-gcp-04-dacd550359a7` | [`checkguard/app/firestore_tools.py`](file:///config/Desktop/BuildWithGemini/checkguard/app/firestore_tools.py) |
| **Google Cloud Storage (GCS)** | Object storage bucket hosting public marketing assets, generated storefront graphics, and motion video clips. | Bucket: `gs://checkguard-media-5835` | [`checkguard/app/agent.py`](file:///config/Desktop/BuildWithGemini/checkguard/app/agent.py#L295-L415) |
| **Agent Platform Sandbox Code Executor** | Isolated container sandbox executing Python code for dynamic fee tables, risk adjustments, and statistical formulas. | Resource: `projects/1069102362772/locations/us-central1/agentSandboxes/checkguard-sandbox` | [`checkguard/app/agent.py`](file:///config/Desktop/BuildWithGemini/checkguard/app/agent.py#L430-L440) (`AgentEngineSandboxCodeExecutor`) |
| **Google Cloud Run (Fully Managed)** | Serverless container runtime hosting the FastAPI proxy and web frontend with auto-scaling and HTTPS ingress. | Service: `checkguard-frontend`<br>Revision: `checkguard-frontend-00002-xxl`<br>Region: `us-central1` | [`checkguard/frontend/main.py`](file:///config/Desktop/BuildWithGemini/checkguard/frontend/main.py), [`checkguard/frontend/Dockerfile`](file:///config/Desktop/BuildWithGemini/checkguard/frontend/Dockerfile) |
| **Artifact Registry** | Container image repository for Cloud Run source builds. | `us-central1-docker.pkg.dev/qwiklabs-gcp-04-dacd550359a7/cloud-run-source-deploy/checkguard-frontend` | Cloud Build pipeline |
| **Cloud Build** | Automated container image compilation and container push triggers during deployment. | Builds in `us-central1` | `gcloud run deploy --source` |
| **Cloud Logging** | Centralized observability, request logging, error reporting, and audit trails for both agent turns and frontend requests. | Resource: `cloud_run_revision` & `reasoning_engine` | `checkguard-frontend` logs |
| **Cloud IAM** | Access control ensuring secure communication between Cloud Run and Agent Engine. | Service Account: `1069102362772-compute@developer.gserviceaccount.com`<br>Role: `roles/aiplatform.user` | IAM Policy Bindings |
| **Google Maps Geocoding API** | Validates issuer physical street addresses on checks against real-world geographical coordinates. | Maps API Key via Vertex AI tool integration | [`checkguard/app/agent.py`](file:///config/Desktop/BuildWithGemini/checkguard/app/agent.py#L140-L195) (`geocode_address`) |
| **Google Places API (New)** | Locates local bank branches, commercial centers, and maker facilities in the vicinity of check issuing addresses. | Places API endpoint (`places.googleapis.com`) | [`checkguard/app/agent.py`](file:///config/Desktop/BuildWithGemini/checkguard/app/agent.py#L198-L253) (`find_nearby_places`) |

---

## 🛠️ External APIs & Protocols

| External Service / Standard | Role in CheckGuard | Implementation Details |
| :--- | :--- | :--- |
| **FDIC BankFind Suite API** | Validates bank legitimacy, FDIC insurance status, charter type, and active operating status using bank name or routing info. | Public FDIC REST endpoint: `https://banks.data.fdic.gov/api/institutions` |
| **A2A Protocol (Agent-to-Agent)** | Standardized message exchange format between frontend proxy and backend agent runtime, supporting multi-turn task contexts and streaming artifacts. | Python SDK `a2a-sdk` (v0.3.26 / v1.1.2) |
| **A2UI v0.8 Specification** | Declarative schema for rendering rich interactive chat components (`Card`, `Column`, `Row`, `Text`, `Image`) in the client UI. | `A2uiSchemaManager(version="0.8")` + `BasicCatalog` |

---

## 🚀 Future Enhancements: Target GCP Services

This section maps upcoming features to the recommended Google Cloud services:

### 1. Multimodal OCR Check Scanning
- **Target Service**: **Vertex AI Multimodal Vision (`gemini-2.5-flash` / `gemini-3.6-flash`)** and **Google Cloud Document AI (Lending / Financial OCR)**.
- **Planned Capability**: Direct upload of raw check images to detect MICR routing numbers, signature lines, handwriting variations, and watermarks.

### 2. FinCEN Regulatory Compliance (CTR & SAR)
- **Target Service**: **Google Cloud Firestore TTL / Audit Logs** + **Cloud Tasks / Cloud Functions**.
- **Planned Capability**: Trigger automated Currency Transaction Reports (CTR) when cash disbursements exceed $10,000, and flag Suspicious Activity Reports (SAR) based on structured behavior rules.

### 3. State & Local Statutory Fee Compliance Matrix
- **Target Service**: **Vertex AI RAG Engine (Vector Search & Corpus)**.
- **Planned Capability**: Grounding agent fee calculations on state banking regulations and local maximum fee statutes using serverless vector search.

### 4. Enterprise Audit Trail & Analytics
- **Target Service**: **BigQuery Export via Firestore Extensions**.
- **Planned Capability**: Streaming transactional check decision records directly to BigQuery for SQL analytics, compliance dashboards, and fraud pattern detection.
