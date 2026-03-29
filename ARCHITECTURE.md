# ARCHITECTURE.md — System Design, Data Flow & Integration Logic

## The Core Problem Being Solved

India mandated the Grameen Credit Score (GCS) in 2025 for rural lending, but banks have zero tooling to compute it. Traditional CIBIL scoring fails for 86% of Indian farmers who are small/marginal with thin credit files. The GCS framework requires using alternative data — savings habits, utility payments, government scheme participation, seasonal income patterns — that no existing tool aggregates or scores. KrishiRin is the operational bridge between that policy mandate and actual bank usage.

## System Design Principles

**Principle 1: ML does the intelligence, LLM does the communication.** Credit scoring uses deterministic ML models (Spark MLlib) for reproducible, fast, explainable scores. LLMs (GPT-4o-mini) are used for scheme eligibility reasoning (RAG), strategy generation, agricultural advisory, and voice communication. This gives deterministic scores with fast inference while keeping the human-facing layer natural and multilingual.

**Principle 2: Databricks is the data backbone, not just storage.** Every data operation uses Delta Lake with meaningful operations — MERGE for upserts, time-travel for audit trails, window functions for seasonal analysis.

**Principle 3: Voice runs outside Databricks, data stays inside.** The voice pipeline (Pipecat + Sarvam) requires persistent WebSocket connections and real-time audio streaming — incompatible with notebook-based execution. It runs on the local machine but reads farmer data via the Databricks SQL connector.

**Principle 4: Indian-first model selection.** Sarvam for STT/TTS (not Whisper or Google Cloud Speech). These models handle Hindi code-mixing, regional accents, and Indian document formats better.

---

## Current Implementation: Three-Service Architecture

The system is implemented as three services running locally:

### 1. Backend — FastAPI Server (`backend/`)
- **server.py** (574 lines): Main application. Serves REST API, manages WebRTC voice connections, runs agent pipelines, streams events via SSE.
- **bot_understanding.py** (57 lines): Builds system prompt for Call 1 (verification/understanding).
- **bot_advisory.py** (192 lines): Builds system prompt + LLM function tool schemas for Call 2 (advisory).
- **databricks_client.py** (111 lines): Singleton wrapper around databricks-sql-connector for all Delta table reads/writes.
- Runs at `http://localhost:8000`

### 2. Frontend — Next.js Web App (`frontend/`)
- **Framework**: Next.js 15 + React 19 + Tailwind CSS
- **Voice**: Pipecat client SDK (@pipecat-ai/client-js, @pipecat-ai/client-react, @pipecat-ai/voice-ui-kit)
- **Charts**: Recharts 3.8.1 (pie charts, bar charts for agent result visualization)
- **State**: Zustand 5.0.0 + React Context (ApplicationContext)
- **Pages**: 6 routes (Dashboard, Profile, Processing, Understanding Call, Advisory Call, Summary)
- **Components**: 25+ components across layout, forms, results, voice, and agent visualization
- Runs at `http://localhost:3000`, proxies `/api/*` to backend

### 3. Agent Pipelines — krishirin_agents (`krishirin_agents/`)
- **precall/**: 11 Google ADK agents in 6 stages (SequentialAgent + ParallelAgent)
- **oncall/**: 8+ agents in 3 stages with 3 parallel tracks
- **voice_server/**: Standalone FastAPI + VoiceSession for testing
- **shared/**: Config, Delta client, weather client, FAISS client, sample data
- Imported by backend as a Python package

---

## End-to-End Data Flow

### Phase 1: Application & Profile (Frontend → Backend)

1. **Farmer fills form** on `/profile` page → `POST /api/application`
   - Input: name, aadhaar_last4, state, district, land_holding_acres, land_type, crops[]
   - Output: `{ farmer_id: "farmer_xxxxx" }`
   - Stored in backend's in-memory `applications` dict

2. **Document upload** → `POST /api/documents/upload`
   - Input: FormData { file, doc_type, farmer_id }
   - Output: `{ document_id, status: "uploaded" }`
   - Files saved to `uploads/` directory, metadata tracked in application

### Phase 2: Precall Analysis (Backend → ADK Agents → Delta)

3. **Trigger analysis** → `POST /api/application/{farmer_id}/analyze`
   - Launches `run_precall_pipeline(farmer_id)` as background task
   - Imports `krishirin_agents.precall.coordinator.agent.root_agent`
   - Creates in-memory ADK session, feeds farmer_id
   - 11 agents run across 6 stages (see AGENTS.md)
   - Progress tracked: 10% + (num_agents_complete × 12)

4. **Frontend polls status** → `GET /api/application/{farmer_id}/pipeline-status`
   - Returns: `{ agents: [{name, status}], overall_progress: 0-100 }`
   - 5 named agents: EligibilityChecker, GrameenScorer, GapAnalyzer, StrategyArchitect, AgriAdvisor
   - Demo mode: Simulates progress with 1.5s intervals

### Phase 3: Understanding Call (Frontend ↔ Backend via WebRTC)

5. **Initiate voice call** → `POST /api/offer` with `{ sdp, type, call_type: "understanding", farmer_id }`
   - Backend creates SmallWebRTCConnection with STUN servers
   - Launches Pipecat pipeline: SmallWebRTCTransport → SarvamSTT → GPT-4o-mini → SarvamTTS
   - System prompt from `bot_understanding.build_understanding_system_prompt(farmer_context)`
   - Bot asks verification questions, farmer answers in Hindi
   - Returns SDP answer + pc_id for WebRTC negotiation

6. **Call complete** → `POST /api/application/{farmer_id}/call1-complete`
   - Updates application phase to "processing"

### Phase 4: Advisory Call with Live Agent Analysis (Frontend ↔ Backend ↔ ADK Agents)

7. **Initiate advisory call** → `POST /api/offer` with `{ sdp, type, call_type: "advisory", farmer_id }`
   - Pipecat pipeline with LLM function tools registered
   - System prompt from `bot_advisory.build_advisory_system_prompt(farmer_context, results)`
   - Session registered in `_active_call_sessions[farmer_id]`

8. **4-phase conversation**:
   - **Phase A**: LLM asks "Kitne ka loan chahiye?" and "Kaun si fasal?"
   - **Phase B**: LLM calls `trigger_oncall_analysis(summary)` → backend spawns oncall pipeline (8+ agents)
   - **Phase C**: LLM makes small talk, calls `check_analysis_status()` periodically
   - **Phase D**: LLM calls `get_analysis_results()` → presents loan terms, crop plan, cashflow

9. **Real-time events** → `GET /api/events/{farmer_id}` (SSE stream)
   - Frontend subscribes to agent completion events
   - Renders AgentResultsPanel with expandable cards + charts
   - Events: `agent_update`, `pipeline_complete`, `pipeline_error`, `heartbeat`

### Phase 5: Results & Summary

10. **Fetch results** → `GET /api/application/{farmer_id}/results`
    - Returns complete AllResults: score, loan_strategy, schemes, agri_advisory, gap_analysis
    - Frontend stores in ApplicationContext

11. **Summary page** (`/summary`) displays:
    - GrameenScoreCard (score gauge, risk category, factors)
    - LoanStrategyCard (product, amount, EMI, harvest-aligned schedule)
    - SchemeEligibilityCard (government schemes with match %)
    - AgriAdvisoryCard (sowing plan, input costs, weather, market timing)
    - RepaymentCashflow (12-month income vs EMI table)

---

## API Endpoints (14 total)

### Application Management
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/application` | Create new farmer application |
| POST | `/api/documents/upload` | Upload farmer documents (FormData) |
| POST | `/api/application/{farmer_id}/analyze` | Trigger precall agent pipeline |
| GET | `/api/application/{farmer_id}/status` | Get application progress |
| POST | `/api/application/{farmer_id}/call1-complete` | Mark Call 1 done |

### Data Retrieval
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/application/{farmer_id}/briefing` | Pre-call briefing (farmer, score, flags, questions) |
| GET | `/api/application/{farmer_id}/results` | All agent results (score, loan, schemes, agri, gaps) |
| GET | `/api/application/{farmer_id}/pipeline-status` | Agent pipeline progress |
| GET | `/api/application/{farmer_id}/transcripts` | Call transcripts (stubbed) |

### Voice & Real-time
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/offer` | WebRTC SDP offer/answer for voice calls |
| GET | `/api/events/{farmer_id}` | SSE stream of agent completion events |
| GET | `/api/call/{farmer_id}/session` | Get active call session ID |

### System
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/health` | Health check + Databricks config status |

---

## Delta Lake Table Design

Tables follow the medallion architecture (Bronze → Silver → Gold) with Scored, Output, and Audit layers.

### Tables Referenced in Current Code

| Table | Layer | Purpose | Read By | Written By |
|-------|-------|---------|---------|------------|
| `silver_farmer_profile` | Silver | Farmer demographics, land, crops, loans, bank summary | data_loader, backend briefing | Data pipeline |
| `scored_profiles` | Scored | ML outputs: grameen_score, risk_category, repayment_prob, risk_cluster, predicted_capacity, factors | data_loader, backend briefing | ML scoring notebook |
| `silver_district_features` | Silver | District agricultural metrics (yield, irrigation, rainfall, soil) | data_loader | Data pipeline |
| `silver_crop_calendar` | Silver | Sowing/harvest windows, seed rates, fertilizer, water per crop per zone | data_loader | Data pipeline |
| `bronze_msp_prices` | Bronze | MSP per quintal for 22 crops | data_loader | Bronze ingestion |
| `precall_analysis` | Output | Complete precall agent pipeline output | Voice agent | precall_synthesis agent |
| `loan_strategies` | Output | Recommended loan terms per farmer | Backend results API | loan_strategy agent |
| `agri_advisory_plans` | Output | Agricultural advisory (sowing plan, costs, market, cashflow) | Backend results API | agri_advisory agents |
| `conversation_log` | Audit | Voice call transcripts (farmer_id, turn, speaker, text, timestamp) | Dashboard | Backend (during calls) |

### Additional Tables (Design/Bronze)
| Table | Layer | Purpose |
|-------|-------|---------|
| `bronze_farmer_raw` | Bronze | Raw uploaded documents |
| `bronze_home_credit` | Bronze | Kaggle dataset (307K loans) |
| `bronze_icrisat_crops` | Bronze | ICRISAT agriculture data |
| `bronze_crop_production` | Bronze | data.gov.in crop stats |
| `gold_credit_features` | Gold | 42 ML features per farmer |
| `gold_train` / `gold_test` | Gold | Train/test splits |
| `scheme_eligibility` | Output | Eligible schemes per farmer |

---

## Where Each Technology Runs

### Local Machine — Backend Server
FastAPI (uvicorn) running at `localhost:8000`. Handles all API requests, WebRTC voice pipeline orchestration, ADK agent execution, and SSE event streaming. Connects to Databricks via SQL connector when configured.

### Local Machine — Frontend
Next.js dev server at `localhost:3000`. Proxies `/api/*` to backend. All UI rendering, voice client (Pipecat SDK + WebRTC), and data visualization (Recharts).

### Local Machine — Agent Pipelines
`krishirin_agents` package imported by backend. Google ADK agents execute via LiteLLM → OpenAI API calls. FAISS index loaded in-process. Weather data fetched via OpenWeatherMap API.

### Databricks (When Configured)
Delta Lake tables for persistent storage. ML training/scoring notebooks. MLflow experiment tracking. When not configured (`USE_SAMPLE_DATA=True`), the system falls back to hardcoded sample data (Ramesh Patil, Nashik).

### External APIs
- **OpenAI**: GPT-4o-mini for agent reasoning and voice LLM (billed per token)
- **Sarvam AI**: STT (Saaras v3) and TTS (Bulbul v3) for Hindi voice (Mumbai servers)
- **OpenWeatherMap**: Weather data for farmer's district (free tier, 1000 calls/day)

---

## Voice Pipeline Architecture

```
FARMER'S MICROPHONE (Browser)
     ↓
SmallWebRTCTransport (receives audio frames)
     ↓
SarvamSTTService (saaras:v3, Hindi speech → English text)
     ↓
LLMUserAggregator (collects user utterances)
     ↓
OpenAILLMService (gpt-4o-mini, text → response)
     │
     ├─ [Advisory Call Only] Function tools available:
     │   trigger_oncall_analysis, check_analysis_status, get_analysis_results
     ├─ If function call → handle_function_call() → spawns/polls agents
     └─ Generates response text
     ↓
SarvamTTSService (bulbul:v3, voice "shubh", English/Hindi text → Hindi audio)
     ↓
SmallWebRTCTransport (sends audio frames)
     ↓
FARMER'S SPEAKER (Browser)
```

**VAD**: SileroVADAnalyzer detects end of farmer's speech.

---

## Frontend Page Architecture

| Route | Page | Key Components | Data Sources |
|-------|------|----------------|-------------|
| `/` | Dashboard | Score card, workflow progress, factors | GET /briefing, GET /results |
| `/profile` | Profile & Docs | FarmerInfoForm, DocumentUpload | POST /application, POST /upload |
| `/processing` | Pipeline Progress | Agent cards, progress bar, GrameenScoreCard | GET /pipeline-status (poll 3s) |
| `/call/understanding` | Understanding Call | VoiceCallInterface, PlasmaVisualizer, LiveTranscript | POST /offer (WebRTC) |
| `/call/advisory` | Advisory Call | VoiceCallInterface, AgentResultsPanel, AgentResultCard, AgentDetailRenderer | POST /offer (WebRTC), GET /events (SSE) |
| `/summary` | Final Results | GrameenScoreCard, LoanStrategyCard, SchemeEligibilityCard, AgriAdvisoryCard, RepaymentCashflow | Context (cached results) |

**AgentDetailRenderer** maps agent output keys to specialized visualizations:
- `optimal_policy` → Loan terms + EMI pie chart + application steps
- `agri_advisory` → Crop allocation pie chart + revenue bar chart + sowing table
- `cashflow_map` → 12-month income vs EMI bar chart + surplus/deficit badges
- `risk_plan` → Risk gauge + mitigation actions with priority colors
- `call_insights` → Acceptance status + stated requirements
- `scheme_matches` → Eligible schemes table
- `bank_products` → Bank comparison table

---

## Integration Points and Gotchas

**Gotcha 1: Databricks availability.** When Databricks credentials are not configured (DATABRICKS_HOST/TOKEN/HTTP_PATH empty), the entire system falls back to sample data via `USE_SAMPLE_DATA=True`. The system is fully functional in demo mode without Databricks.

**Gotcha 2: SmallWebRTC vs Daily.co.** The current implementation uses Pipecat's SmallWebRTC transport (browser-native WebRTC with STUN servers) instead of Daily.co rooms. No Daily.co account needed. STUN server: `stun:stun.l.google.com:19302`.

**Gotcha 3: OpenAI as primary LLM.** Despite CLAUDE.md's original design specifying Gemini 2.0 Flash, the actual implementation uses OpenAI GPT-4o-mini everywhere — both in ADK agents (via LiteLLM) and in the voice pipeline (via OpenAI SDK directly). `OPENAI_API_KEY` is the critical API key.

**Gotcha 4: In-memory state.** The backend stores applications, pipeline statuses, and call sessions in Python dictionaries (not in a database). This is a hackathon demo pattern — all state is lost on server restart.

**Gotcha 5: Frontend proxy.** Next.js config rewrites `/api/*` to `http://localhost:8000`. Both servers must be running for the frontend to work.

**Gotcha 6: SSE event streaming.** The advisory call's real-time agent panel depends on the SSE endpoint (`/api/events/{farmer_id}`). The endpoint waits up to 120s for the call session to start, then streams events from the oncall_runner's event queue with a 30s idle timeout.

**Gotcha 7: SQL connector latency.** Databricks SQL connector adds ~200-500ms per query. All farmer data is pre-loaded into the system prompt BEFORE the voice call starts. Conversation logging happens asynchronously (fire-and-forget).

**Gotcha 8: Two Databricks clients.** `backend/databricks_client.py` (used by server.py for API endpoints) and `krishirin_agents/shared/delta_client.py` (used by ADK agents) are separate implementations. Both connect via databricks-sql-connector with the same credentials.

--

## Demonstration Flow (What the User Sees)

1. Open browser → Next.js dashboard at `localhost:3000`
2. Navigate to `/profile` → Fill farmer details + upload documents
3. Dashboard shows farmer profile with Grameen score and workflow progress
4. Navigate to `/call/understanding` → Voice call starts in Hindi
5. Bot asks verification questions, farmer answers → Call ends
6. Navigate to `/processing` → Watch 5 agents complete (progress bar fills)
7. Navigate to `/call/advisory` → Advisory call starts
8. **HERO MOMENT**: Bot asks 2 questions, triggers agents in background
9. Side panel shows agent results appearing in real-time with charts
10. Bot presents: "Aapke liye ₹2 lakh KCC loan, 4% interest, EMI ₹6,500. Soybean 1.5 acre, cotton 1 acre lagaaiye..."
11. Navigate to `/summary` → Full results: score card, loan terms, crop plan, 12-month cashflow
