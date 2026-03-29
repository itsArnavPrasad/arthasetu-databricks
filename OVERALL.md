# OVERALL.md — KrishiRin (कृषिऋण) Complete Project Overview

## What is KrishiRin?

KrishiRin is an AI-powered **Grameen Credit Advisory system** for rural Indian farmers. It computes a Grameen Credit Score using alternative data (savings habits, government scheme participation, seasonal income patterns), proposes optimal loan strategies through a multi-agent pipeline, and delivers personalized financial + agricultural advice to the farmer via **real-time Hindi voice calls**.

Built for the **Databricks BharatBricks Hackathon** (Digital-Artha track). Two-person team.

### The Problem

India mandated the **Grameen Credit Score (GCS)** in 2025 for rural lending, but banks have zero tooling to compute it. Traditional CIBIL scoring fails for **86% of Indian farmers** who are small/marginal with thin credit files. Meanwhile, 16% of agricultural loans become NPAs — not because farmers can't get loans, but because they get **no post-disbursement support** on how to repay them.

### The Solution

KrishiRin bridges this gap in three ways:
1. **Computes Grameen Credit Scores** using alternative data that traditional scoring ignores (savings habits, PM-KISAN enrollment, seasonal income patterns, land productivity)
2. **Designs personalized loan strategies** aligned to the farmer's harvest cycle — EMI is due when the farmer has money, not in lean months
3. **Calls the farmer in Hindi** to explain loan terms, advise on crop planning, and coach toward financial success — because 70% of Indian farmers don't use apps

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Data Platform** | Databricks Delta Lake | All data storage, Bronze/Silver/Gold medallion architecture |
| **Data Processing** | PySpark | Feature engineering (42 features), data transformations |
| **ML Models** | Spark MLlib (GBTClassifier, KMeans, RandomForestRegressor) | 3-model ensemble for Grameen scoring |
| **ML Tracking** | MLflow | Experiment logging, model registry, metrics comparison |
| **Agent Framework** | Google ADK (Agent Development Kit) | 19+ agents across 2 pipelines (precall + oncall) |
| **Agent LLM** | OpenAI GPT-4o-mini via LiteLLM | Reasoning engine for all ADK agents |
| **Voice Framework** | Pipecat | Real-time voice pipeline orchestration |
| **Speech-to-Text** | Sarvam AI Saaras v3 | Hindi/Hinglish speech recognition (Indian-made) |
| **Text-to-Speech** | Sarvam AI Bulbul v3 | Natural Hindi speech synthesis, voice "shubh" (Indian-made) |
| **Voice LLM** | OpenAI GPT-4o-mini | Conversational intelligence for voice calls |
| **Voice Transport** | SmallWebRTC | Browser-native WebRTC audio (no Daily.co needed) |
| **RAG** | FAISS + sentence-transformers (all-MiniLM-L6-v2) | Semantic search over government scheme documents |
| **Backend** | FastAPI + uvicorn | REST API (14 endpoints), WebRTC, SSE event streaming |
| **Frontend** | Next.js 15 + React 19 + Tailwind CSS | 6-page web app with voice UI and data visualizations |
| **Charts** | Recharts | Pie charts, bar charts, gauges for agent result visualization |
| **State Management** | Zustand + React Context | Application state across pages |
| **Voice UI** | Pipecat Client SDK | PlasmaVisualizer (waveform), LiveTranscript, WebRTC client |
| **Weather API** | OpenWeatherMap | Live weather for farmer's district (free tier) |
| **Database Connector** | databricks-sql-connector | Local machine → Databricks Delta Lake reads/writes |

### Indian-Made Models (Hackathon Bonus)
- **Sarvam Saaras v3** (STT) — supports 22 Indian languages, code-mixing, 70ms latency
- **Sarvam Bulbul v3** (TTS) — 25+ Indian voices, handles ₹ formatting, Hindi-English switching

---

## Data Sources (11 Datasets)

### Primary Training Data

| # | Dataset | Source | Size | Purpose |
|---|---------|--------|------|---------|
| 1 | **Home Credit Default Risk** | Kaggle | 307K loans | Primary ML training — loan default prediction with alternative data features |
| 2 | **ICRISAT District-Level Database** | ICRISAT/Cornell | 571 districts, 1030 variables, 11M+ data points | District-level crop yields, rainfall, irrigation, land holdings |
| 3 | **Crop Production Statistics** | data.gov.in | All India districts | District-wise, crop-wise area and production (1997–present) |
| 4 | **MSP (Minimum Support Prices)** | Government of India | 22 crops | Guaranteed minimum price per quintal per crop per year |

### Enrichment & Reference Data

| # | Dataset | Source | Purpose |
|---|---------|--------|---------|
| 5 | **Synthetic UPI Transactions** | Hackathon organizers | Financial feature engineering from transaction-level data |
| 6 | **Agriculture Loan Disbursement** | data.gov.in | Calibrate realistic loan amount distributions per state |
| 7 | **Indian Agriculture Comprehensive** | Kaggle | Cost of cultivation per crop for expense estimation |
| 8 | **Government Scheme Documents** | KCC, PMFBY, PM-KISAN, MUDRA, RBI GCS | RAG knowledge base for scheme eligibility reasoning |
| 9 | **Live Weather Data** | OpenWeatherMap API | Real-time conditions + 7-day forecast for farmer's district |
| 10 | **Crop Calendar & Practices** | ICAR, KVK, state agricultural universities | Sowing windows, seed rates, fertilizer doses, water needs per crop per zone |
| 11 | **Agro-Climatic Zone Mapping** | Planning Commission / ICAR | Maps each district to one of 15 agro-climatic zones |

### Synthetic Data Augmentation
- **5,000 synthetic farmer profiles** with 12 months of transaction data each
- Parameterized by real NABARD, RBI, and ICRISAT statistics
- Farmer archetypes: 55% small/marginal, 25% medium, 10% large, 10% landless-allied
- Default rates calibrated to RBI NPA data (16-18% for small/marginal, 5% for large)
- Seasonal income patterns match India's actual Kharif/Rabi agricultural cycle

---

## End-to-End System Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATABRICKS PLATFORM                         │
│                                                                    │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌─────────────┐  │
│  │  Bronze   │───▶│  Silver  │───▶│   Gold   │───▶│   Scored    │  │
│  │  Tables   │    │  Tables  │    │ Features │    │  Profiles   │  │
│  │           │    │          │    │(42 cols) │    │             │  │
│  │ Raw CSVs  │    │ Cleaned  │    │ PySpark  │    │ Spark MLlib │  │
│  │ Excels    │    │ Joined   │    │ Feature  │    │ 3-Model     │  │
│  │ APIs      │    │ Imputed  │    │ Eng.     │    │ Ensemble    │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────┬──────┘  │
│                                                          │         │
│  MLflow: 6 experiments logged, best model registered     │         │
└──────────────────────────────────────────────────────────┼─────────┘
                                                           │
                    ┌──────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      LOCAL MACHINE (3 Services)                     │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ BACKEND — FastAPI (localhost:8000)                             │ │
│  │                                                                │ │
│  │  ┌─────────────────┐  ┌───────────────────────────────────┐   │ │
│  │  │ Precall Pipeline │  │     Voice Pipeline (Pipecat)      │   │ │
│  │  │ 11 ADK Agents    │  │                                   │   │ │
│  │  │ 6 Stages         │  │  Mic → SmallWebRTC → SarvamSTT   │   │ │
│  │  │ Google ADK +     │  │      → GPT-4o-mini → SarvamTTS   │   │ │
│  │  │ LiteLLM/OpenAI   │  │      → SmallWebRTC → Speaker     │   │ │
│  │  └────────┬────────┘  │                                   │   │ │
│  │           │           │  Advisory call triggers:           │   │ │
│  │           ▼           │  ┌──────────────────┐              │   │ │
│  │  ┌────────────────┐   │  │ Oncall Pipeline   │              │   │ │
│  │  │ Results stored  │   │  │ 8+ ADK Agents    │              │   │ │
│  │  │ in Delta tables │   │  │ 3 Parallel Tracks│              │   │ │
│  │  └────────────────┘   │  └──────────────────┘              │   │ │
│  │                       └───────────────────────────────────┘   │ │
│  │  14 REST API endpoints + SSE event streaming + WebRTC         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ FRONTEND — Next.js 15 (localhost:3000)                        │ │
│  │                                                                │ │
│  │  Dashboard → Profile → Processing → Understanding Call        │ │
│  │                                     → Advisory Call → Summary │ │
│  │                                                                │ │
│  │  Voice UI: PlasmaVisualizer + LiveTranscript                  │ │
│  │  Agent UI: Real-time cards with Recharts visualizations       │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Flow — What Happens Step by Step

### Step 1: Data Ingestion & Feature Engineering (Databricks)

Raw datasets are loaded into **Bronze** Delta tables (raw CSVs/Excels). Transformed into **Silver** tables (cleaned, typed, joined, null-imputed). Feature engineering in PySpark produces the **Gold** table with **42 features** across 5 families:

| Family | Features | What They Capture |
|--------|----------|-------------------|
| Income & Cash Flow (1-12) | Avg/median income, trend, seasonality index, Kharif/Rabi income, off-season ratio, gap months, govt transfers, source diversity | How much the farmer earns and how stable |
| Expenditure & Debt (13-22) | DTI ratio, EMI pattern detection, expense-income correlation | How much they owe, can they handle more |
| Savings & Behavior (23-30) | Savings rate, balance recovery speed, banking relationship length | Financial discipline and resilience |
| Agricultural & Land (31-38) | Land productivity estimate, irrigation access, district crop risk index | Productive capacity |
| Scheme & History (39-42) | Repayment history score, government scheme participation | Track record |

### Step 2: ML Scoring (Databricks + Spark MLlib)

A **3-model ensemble** runs on the Gold features:

| Model | Algorithm | Question Answered | Output |
|-------|-----------|-------------------|--------|
| Model 1 | GBTClassifier | "Will this farmer repay?" | Repayment probability (0-1) |
| Model 2 | KMeans (k=4) | "What risk cluster does this farmer belong to?" | Risk cluster (0-3), handles thin-file farmers |
| Model 3 | RandomForestRegressor | "How much can this farmer repay?" | Predicted loan capacity (₹) |

**Grameen Composite Score** = (0.40 × repayment_prob) + (0.25 × normalized_risk_score) + (0.35 × capacity_score), scaled 0-100.

**Risk Categories**: A (≥75, Low), B (55-74, Moderate), C (35-54, Elevated), D (<35, High).

Results written to `scored_profiles` Delta table. **6 MLflow experiments** logged (Logistic Regression → GBT tuned → GBT + CV → GBT + feature selection).

### Step 3: Precall Agent Pipeline (Google ADK, 11 Agents)

Triggered via `POST /api/application/{farmer_id}/analyze`. Reads pre-computed ML scores from Delta — **agents never call ML models directly**.

```
Stage 1: Data Loader — loads farmer profile, ML scores, district data,
         crop calendar, MSP prices, live weather (6 tools)

Stage 2: 6 agents in PARALLEL
         ├── Score Explainer → plain-language credit assessment
         ├── Risk Flag Detector → financial, agricultural, documentation flags
         ├── Market Research → mandi prices, pest alerts, scheme updates
         ├── Scheme RAG Agent → FAISS search over scheme documents (4 queries)
         ├── Scheme Web Agent → latest scheme updates from LLM knowledge
         └── Eligibility Evaluator → rule-based KCC/PMFBY/PM-KISAN/MUDRA check

Stage 3: Scheme Synthesizer → merges 3 scheme sources into unified report

Stage 4: Gap Analyzer → critical gaps, warnings, improvement suggestions

Stage 5: Loan Strategy Architect → optimal product, amount, tenure, EMI,
         harvest-aligned repayment schedule

Stage 6: Precall Synthesis → final briefing document, writes to Delta
```

### Step 4: Understanding Call (Voice Call 1)

**Purpose**: Verify farmer details and investigate risk flags. No loan recommendations.

- Farmer opens browser → clicks "Call Shuru Karein"
- WebRTC audio connection via SmallWebRTC
- Pipeline: Farmer speaks Hindi → **Sarvam STT** → English text → **GPT-4o-mini** (with farmer context in system prompt) → response → **Sarvam TTS** → Hindi audio back to farmer
- Bot asks verification questions naturally, never revealing flags
- Hindi/Hinglish, respectful "aap" form, 2-3 sentences max per response
- Frontend shows PlasmaVisualizer (waveform) + LiveTranscript

### Step 5: Advisory Call (Voice Call 2) — The Hero Moment

**Purpose**: Understand farmer's actual needs, run live analysis, present personalized recommendations.

**4-Phase Conversation**:

| Phase | What Happens | Duration |
|-------|-------------|----------|
| **A — Clarification** | Bot asks: "Kitne ka loan chahiye?" and "Kaun si fasal ugaane ka plan hai?" | ~30s |
| **B — Trigger** | Bot calls `trigger_oncall_analysis()` → spawns 8+ agents in background | Instant |
| **C — Small Talk** | Bot asks about farming/weather while agents run. Polls `check_analysis_status()` | ~10s |
| **D — Results** | Bot calls `get_analysis_results()` → presents loan terms, crop plan, cashflow conversationally | ~2min |

**Oncall Pipeline** (8+ agents, 3 parallel tracks, triggered during the call):

```
Stage 1: Call Transcript Analyzer → extracts farmer's stated needs

Stage 2: 3 PARALLEL tracks
         ├── Track A: Loan Policy Pipeline
         │   ├── Scheme Matcher + Bank Product Agent (parallel)
         │   └── Policy Optimizer → best scheme + bank + terms
         │
         ├── Track B: Agricultural Advisory Pipeline
         │   ├── Crop Planner → sowing plan per crop
         │   ├── Input Cost + Market Timing agents (parallel)
         │   └── Agri Synthesizer → comprehensive advisory
         │
         └── Track C: Risk Mitigator → insurance, diversification, buffers

Stage 3: Cashflow Mapper → 12-month income vs EMI projection
```

**Real-time Frontend**: While agents run, SSE events stream agent completion to the AgentResultsPanel — expandable cards appear with charts (loan EMI pie chart, crop allocation pie, revenue bars, cashflow bar chart, risk gauge).

### Step 6: Summary & Results

Full results displayed on the summary page:
- **Grameen Score Card** — score gauge, risk category, contributing factors
- **Loan Strategy Card** — recommended product, amount, EMI, harvest-aligned schedule
- **Scheme Eligibility Card** — government schemes with match percentage
- **Agricultural Advisory Card** — sowing plan, input costs, weather guidance, market timing
- **Repayment Cashflow** — 12-month income vs EMI table with surplus/deficit

---

## Delta Lake Table Architecture

All data flows through Databricks Delta Lake using the **medallion architecture**:

| Layer | Tables | Purpose |
|-------|--------|---------|
| **Bronze** | `bronze_farmer_raw`, `bronze_home_credit`, `bronze_icrisat_crops`, `bronze_crop_production`, `bronze_msp_prices` | Raw ingested data |
| **Silver** | `silver_farmer_profile`, `silver_district_features`, `silver_crop_calendar` | Cleaned, typed, joined, enriched |
| **Gold** | `gold_credit_features`, `gold_train`, `gold_test` | ML-ready features (42 columns) |
| **Scored** | `scored_profiles` | ML output: grameen_score, risk_category, repayment_prob, risk_cluster, predicted_capacity, factors |
| **Output** | `precall_analysis`, `loan_strategies`, `agri_advisory_plans`, `scheme_eligibility` | Agent pipeline results |
| **Audit** | `conversation_log` | Voice call transcripts (farmer_id, turn, speaker, text, timestamp) |

Catalog: `krishirin.loan_advisory`

**Delta Lake features used**: MERGE INTO (incremental updates), Time Travel (audit trail), Schema Evolution, DESCRIBE HISTORY, partition by state, OPTIMIZE.

---

## API Endpoints (14 Total)

### Application Management
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/application` | Create new farmer application |
| POST | `/api/documents/upload` | Upload farmer documents |
| POST | `/api/application/{farmer_id}/analyze` | Trigger precall agent pipeline |
| GET | `/api/application/{farmer_id}/status` | Get application progress |
| POST | `/api/application/{farmer_id}/call1-complete` | Mark Understanding Call done |

### Data Retrieval
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/application/{farmer_id}/briefing` | Pre-call briefing (profile, score, flags, questions) |
| GET | `/api/application/{farmer_id}/results` | All results (score, loan, schemes, agri, gaps) |
| GET | `/api/application/{farmer_id}/pipeline-status` | Agent pipeline progress |
| GET | `/api/application/{farmer_id}/transcripts` | Call transcripts |

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

## Frontend Pages

| Route | Page | Key Features |
|-------|------|-------------|
| `/` | Dashboard | Grameen score card, workflow progress tracker, key factors |
| `/profile` | Profile & Documents | Farmer info form, document upload, Aadhaar verification |
| `/processing` | Pipeline Progress | Animated agent cards, progress bar, score preview |
| `/call/understanding` | Understanding Call | PlasmaVisualizer waveform, live bidirectional transcript |
| `/call/advisory` | Advisory Call | Voice UI + real-time agent results panel with charts |
| `/summary` | Final Results | Score card, loan strategy, schemes, agri advisory, 12-month cashflow |

**Agent Result Visualizations** (Recharts):
- Loan terms with EMI breakdown pie chart
- Crop allocation pie chart + revenue bar chart
- 12-month income vs EMI bar chart with surplus/deficit badges
- Risk gauge with mitigation action cards
- Scheme eligibility comparison table

---

## Project Structure

```
krishirin/
├── backend/                          # FastAPI server (localhost:8000)
│   ├── server.py                     # Main app: 14 endpoints, WebRTC, SSE, pipeline orchestration
│   ├── bot_understanding.py          # System prompt builder for Call 1
│   ├── bot_advisory.py               # System prompt + function tools for Call 2
│   └── databricks_client.py          # Singleton Databricks SQL wrapper
│
├── frontend/                         # Next.js 15 + React 19 (localhost:3000)
│   ├── src/app/                      # 6 page routes
│   ├── src/components/               # 25+ components (voice, results, forms, layout)
│   └── next.config.js                # API proxy to backend
│
├── krishirin_agents/                 # Google ADK agent pipelines
│   ├── precall/                      # 11 agents, 6 stages
│   │   ├── coordinator/              # Root SequentialAgent
│   │   ├── data_loader/              # Stage 1: 6 Delta/API tools
│   │   ├── score_explainer/          # Stage 2a: Credit score explanation
│   │   ├── risk_flag_detector/       # Stage 2b: Risk flag detection
│   │   ├── market_research/          # Stage 2c: Market intelligence
│   │   ├── scheme_matching/          # Stage 2d-f: RAG + web + eligibility → synthesis
│   │   ├── gap_analyzer/             # Stage 4: Gap analysis + profile validation
│   │   ├── loan_strategy/            # Stage 5: Loan package design
│   │   └── precall_synthesis/        # Stage 6: Final synthesis + Delta write
│   │
│   ├── oncall/                       # 8+ agents, 3 stages
│   │   ├── coordinator/              # Root SequentialAgent
│   │   ├── call_analyzer/            # Stage 1: Transcript analysis
│   │   ├── loan_policy/              # Track A: Scheme matching + bank + optimization
│   │   ├── agri_advisory/            # Track B: Crop plan + costs + market + synthesis
│   │   ├── risk_mitigator/           # Track C: Insurance + diversification + buffers
│   │   └── cashflow_mapper/          # Stage 3: 12-month projection
│   │
│   ├── voice_server/                 # Standalone voice server + oncall runner
│   │   ├── oncall_runner.py          # Pipeline execution + event streaming
│   │   ├── tools.py                  # trigger/check/get analysis functions
│   │   └── models.py                 # CallPhase, AgentStatus, display config
│   │
│   └── shared/                       # Shared infrastructure
│       ├── config.py                 # Models, tables, feature flags
│       ├── delta_client.py           # Databricks SQL functions
│       ├── weather_client.py         # OpenWeatherMap integration
│       ├── faiss_client.py           # FAISS + sentence-transformers RAG
│       └── sample_data.py            # Hardcoded fallback (Ramesh Patil, Nashik)
│
├── CLAUDE.md                         # Project instructions for AI assistants
├── ARCHITECTURE.md                   # System design, API endpoints, component map
├── DATA_PIPELINE.md                  # Datasets, transformations, Delta strategy
├── ML_PIPELINE.md                    # 42 features, 3-model ensemble, MLflow plan
├── AGENTS.md                         # 19+ agent roles, tools, orchestration flow
├── VOICE_PIPELINE.md                 # Two-call voice system, Pipecat + Sarvam
└── ROADMAP.md                        # Hour-by-hour execution plan
```

---

## Key Design Principles

### 1. ML Does the Intelligence, LLM Does the Communication
Credit scoring uses **deterministic ML models** (Spark MLlib) for reproducible, fast, explainable scores. LLMs (GPT-4o-mini) handle scheme eligibility reasoning, strategy generation, agricultural advisory, and voice communication. This gives deterministic scores (~50ms per farmer) with a natural, multilingual human-facing layer.

### 2. Databricks is the Data Backbone
Every data operation uses Delta Lake with meaningful operations — MERGE for upserts, time travel for audit trails, window functions for seasonal analysis. Not just storage — the platform does real work.

### 3. Voice Runs Outside, Data Stays Inside
The voice pipeline (Pipecat + Sarvam) requires persistent WebSocket connections and real-time audio streaming — incompatible with notebook-based execution. It runs on the local machine but reads farmer data via the Databricks SQL connector. All farmer data is pre-loaded into the system prompt before the call starts — no mid-conversation Delta queries.

### 4. Indian-First Model Selection
Sarvam for STT/TTS (not Whisper or Google Cloud Speech). These models handle Hindi code-mixing, regional accents, and Indian number formatting (₹2,00,000 → "do lakh rupaye") better. Earns hackathon bonus points.

### 5. ML Models Run Before Agents, Never Inside Them
The ML scoring notebook is self-contained. It writes to `scored_profiles`. Agents only read from that table. No agent ever invokes a Spark MLlib model directly. This keeps ML independently testable and batch-capable.

---

## Latency Design

| Stage | Expected Latency |
|-------|-----------------|
| Farmer speech → Backend (WebRTC) | ~50ms |
| Sarvam STT processing | ~70ms |
| OpenAI GPT-4o-mini first token | ~500-1500ms |
| Sarvam TTS first audio chunk | ~200ms |
| Audio → Farmer browser (WebRTC) | ~50ms |
| **Total end-to-end** | **~900ms - 2s** |

Streaming end-to-end: TTS starts synthesizing as soon as the first words arrive from the LLM. The farmer hears the response while the LLM is still generating.

---

## Conversation Design

- **Language**: Hindi/Hinglish. Respectful "aap" form. Never patronizing.
- **Length**: Every response under 3 sentences. Voice monologues feel unnatural.
- **Numbers**: Concrete ₹ amounts. "₹2 lakh ka loan, ₹6,500 EMI" not "4% per annum."
- **Specificity**: References farmer's actual crops, district, land size — never generic.
- **Repayment tie-in**: Agricultural advice always connects to loan repayment capacity.

---

## Offline/Demo Mode

When Databricks is not configured (`USE_SAMPLE_DATA=True`), the entire system runs fully functional with hardcoded sample data:

**Sample Farmer: Ramesh Patil** — Age 42, Nashik (Maharashtra), 3 acres owned, mixed irrigation, soybean/onion/wheat, existing ₹50K SBI crop loan, PM-KISAN enrolled, Grameen Score 68.5 (Category B, Moderate Risk), predicted capacity ₹2,00,000.

All backend APIs, agent pipelines, and voice calls work without any Databricks connection.

---

## Environment Variables

| Variable | Service | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | Agents + Voice | GPT-4o-mini for all agent reasoning and voice LLM |
| `SARVAM_API_KEY` | Voice | STT (Saaras v3) + TTS (Bulbul v3) for Hindi voice |
| `GOOGLE_API_KEY` | Agents | Gemini (configured but not actively used) |
| `OPENWEATHER_API_KEY` | Agents | Live weather for farmer's district |
| `DATABRICKS_HOST` | Data | Databricks workspace URL |
| `DATABRICKS_TOKEN` | Data | Personal access token |
| `DATABRICKS_HTTP_PATH` | Data | SQL warehouse HTTP path |

---

## How to Run

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev    # runs at localhost:3000

# Open browser → localhost:3000
```

No Databricks or Daily.co account needed for demo mode. SmallWebRTC handles browser-native audio.

---

## Hackathon Differentiators

1. **Voice-first**: Every other team builds a web dashboard. KrishiRin calls the farmer in Hindi.
2. **Agricultural advisory, not just credit scoring**: The voice agent advises on crop planning, input costs, market timing, and weather — all tied to loan repayment capacity.
3. **Two-call architecture**: First call verifies and investigates. Second call advises with live agent analysis running in background.
4. **Real-time agent visualization**: During the advisory call, the frontend shows agent results appearing live with interactive charts.
5. **19+ specialized agents**: Not one monolithic LLM call — a structured pipeline with parallel execution, state passing, and specialized tools.
6. **3-model ML ensemble**: GBT for repayment prediction, KMeans for thin-file behavioral clustering, RF for capacity estimation. All logged to MLflow.
7. **Indian-made models**: Sarvam STT/TTS earn bonus points and genuinely handle Hindi better.
8. **Full Delta Lake usage**: Medallion architecture, MERGE, time travel, schema evolution — not just Delta-as-storage.

---

## Future Vision

Periodic follow-up calls where the AI agent:
- Calls the farmer at sowing time with updated weather + market advice
- Checks mid-season on crop progress and adjusts the plan
- Reminds before harvest about optimal selling timing and MSP procurement
- Follows up after repayment dates to course-correct if needed

The agent **learns** the farmer's evolving situation across calls and adapts advice over time — becoming a trusted agricultural advisor, not just a one-time loan explainer.
