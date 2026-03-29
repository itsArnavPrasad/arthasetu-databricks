# CLAUDE.md — KrishiRin (कृषिऋण)

AI-powered Grameen Credit Advisory system for rural Indian farmers. Hackathon project for Databricks BharatBricks (Digital-Artha track). Two-person team.

## What This Is
A system that builds Grameen Credit Score profiles for farmers using alternative data, proposes loan strategies via a multi-agent pipeline, and conducts advisory calls in Hindi via real-time voice AI. The voice agent goes beyond explaining loan terms — it helps the farmer understand the best repayment strategies, advises on agricultural practices to improve crop yield, and coaches them toward financial success. Future extension: periodic follow-up calls where the agent learns the farmer's evolving situation and adapts advice over time.

## Architecture At A Glance (Strict Sequential Order)
1. Farmer data → Delta Lake (Bronze/Silver/Gold) → PySpark feature engineering (42 features)
2. Spark MLlib (3-model ensemble) runs on Gold features → Grameen Score + all results stored to `scored_profiles` Delta table
3. **Precall agent pipeline** (Google ADK + OpenAI GPT-4o-mini via LiteLLM, 11 agents across 6 stages with parallel execution) reads pre-computed ML results from Delta → enriches with eligibility, gaps, loan strategy, AND a comprehensive agricultural advisory plan
4. **Two voice calls** via Pipecat + Sarvam STT/TTS + SmallWebRTC:
   - **Call 1 (Understanding)**: Bot verifies farmer details, investigates risk flags, gathers context
   - **Call 2 (Advisory)**: Bot asks clarification questions, triggers **oncall agent pipeline** (8+ agents across 3 parallel tracks) in background, then presents results — loan terms, crop plan, cashflow map — conversationally in Hindi
5. Conversation logged to Delta, full results shown on summary page

ML models ALWAYS run before agents. Agents NEVER call ML models — they read stored results from Delta tables.

## Current Implementation Status

### Agent Pipelines Built
- **Precall Pipeline**: 11 agents in 6 stages (SequentialAgent + ParallelAgent orchestration)
  - Stage 1: Data loader (6 tools)
  - Stage 2: 6 agents in PARALLEL (score explainer, risk flag detector, market research, scheme RAG, scheme web, eligibility evaluator)
  - Stage 3: Scheme synthesizer
  - Stage 4: Gap analyzer
  - Stage 5: Loan strategy architect
  - Stage 6: Precall synthesis (writes to Delta)
- **Oncall Pipeline**: 8+ agents in 3 stages, triggered DURING the advisory voice call
  - Stage 1: Call transcript analyzer
  - Stage 2: 3 PARALLEL tracks (loan policy optimization, agricultural advisory, risk mitigation)
  - Stage 3: 12-month cashflow mapper

### Backend Built
- FastAPI server (`backend/server.py`, 574 lines) with 14 REST API endpoints
- WebRTC voice pipeline orchestration via Pipecat SmallWebRTC
- SSE (Server-Sent Events) for real-time agent progress streaming to frontend
- Databricks SQL client with fallback to sample data

### Frontend Built
- Next.js 15 + React 19 web application with 6 pages and 25+ components
- Pages: Dashboard, Profile & Documents, Processing, Understanding Call, Advisory Call, Summary
- Real-time voice UI with Pipecat client SDK (PlasmaVisualizer, LiveTranscript)
- Live agent results panel with Recharts charts (pie, bar) during advisory call
- Full result visualization: Grameen score card, loan strategy, scheme eligibility, agri advisory, cashflow table

### Voice Pipeline Built
- Two-call architecture: Understanding (verification) + Advisory (with live agent analysis)
- Pipecat pipeline: SmallWebRTCTransport → SarvamSTT (saaras:v3) → OpenAI GPT-4o-mini → SarvamTTS (bulbul:v3, voice "shubh") → SmallWebRTCTransport
- Advisory call uses LLM function calling to trigger/poll/fetch oncall agent results
- SileroVAD for voice activity detection

## Mandatory Technology Choices
- **Data**: Databricks Delta Lake. All reads/writes through Delta tables. Catalog: `krishirin.loan_advisory`.
- **Processing**: PySpark only for feature engineering. No pandas for data transformations.
- **ML**: Spark MLlib (GBTClassifier, KMeans, RandomForestRegressor). Every run logged to MLflow.
- **Agents**: Google ADK with LiteLLM wrapping OpenAI GPT-4o-mini. SequentialAgent + ParallelAgent orchestrators. 11 precall agents + 8+ oncall agents.
- **Voice**: Pipecat framework + Sarvam Saaras v3 (STT) + Sarvam Bulbul v3 (TTS) + SmallWebRTC (browser-based WebRTC transport). Runs on local machine, NOT in Databricks.
- **LLM (Voice)**: OpenAI GPT-4o-mini via OpenAI SDK (direct, not via LiteLLM).
- **Frontend**: Next.js 15 + React 19 web application with Tailwind CSS, Recharts, Zustand, Pipecat client SDK.
- **Backend**: FastAPI server with uvicorn. Serves REST API + WebRTC endpoints.
- **RAG**: FAISS + sentence-transformers (all-MiniLM-L6-v2) on DBFS.

## Project Structure
- `backend/` — FastAPI server: voice pipeline orchestration, 14 API endpoints, Databricks SQL client
  - `server.py` — Main FastAPI app (WebRTC, SSE, application management)
  - `bot_understanding.py` — System prompt builder for Call 1 (verification)
  - `bot_advisory.py` — System prompt + LLM function tool schemas for Call 2 (advisory)
  - `databricks_client.py` — Singleton Databricks SQL wrapper
- `frontend/` — Next.js 15 + React 19 web app (6 pages, 25+ components, Recharts visualizations)
- `krishirin_agents/` — Google ADK agent pipelines + shared utilities
  - `precall/` — Precall analysis pipeline (11 agents, 6 stages)
  - `oncall/` — Oncall advisory pipeline (8+ agents, 3 stages with 3 parallel tracks)
  - `voice_server/` — Voice server, oncall runner, event streaming, tools
  - `shared/` — Config (models, tables), delta_client, weather_client, faiss_client, sample_data
  - `api/` — Standalone FastAPI endpoint for precall analysis
  - `deployment/` — Vertex AI deployment scripts

## Critical Rules
1. NEVER hardcode API keys. Use Databricks secrets (`dbutils.secrets.get`) in notebooks, `.env` + `dotenv` locally.
2. ALL data operations go through Delta tables. No local CSVs in the pipeline.
3. Every ML experiment MUST be wrapped in `mlflow.start_run()` with params, metrics, and model logged.
4. Voice pipeline runs OUTSIDE Databricks. It connects to Delta via `databricks-sql-connector`.
5. Use Indian-made models wherever possible (Sarvam STT/TTS). This earns hackathon bonus points.
6. Agents share state via Google ADK's `output_key` → `context.state` mechanism. Key state keys: `farmer_context`, `credit_assessment`, `risk_flags`, `market_research`, `scheme_rag_results`, `scheme_web_results`, `eligibility_evaluation`, `eligibility_report`, `gap_analysis`, `loan_strategy`, `precall_analysis`, `call_insights`, `crop_plan`, `agri_advisory`, `optimal_policy`, `risk_plan`, `cashflow_map`.
7. ML models run BEFORE the agent pipeline, NEVER inside it. The ML scoring notebook writes results to the `scored_profiles` Delta table. The agents then read from that table. No agent should ever invoke a Spark MLlib model directly — agents only read pre-computed scores from Delta.

## Environment Variables
- `OPENAI_API_KEY` — OpenAI GPT-4o-mini (primary LLM for both agents via LiteLLM and voice pipeline)
- `SARVAM_API_KEY` — Sarvam AI (STT via Saaras v3, TTS via Bulbul v3)
- `GOOGLE_API_KEY` — Google Gemini (configured but not actively used in current implementation)
- `OPENWEATHER_API_KEY` — OpenWeatherMap (live weather for farmer's district, free tier 1000 calls/day)
- `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `DATABRICKS_HTTP_PATH` — for local→Databricks connection
- `DAILY_API_KEY` — Daily.co (optional, not used in current SmallWebRTC implementation)

## Detailed Documentation
Read these for each component:
- `ARCHITECTURE.md` — System design, data flow, API endpoints, component map, table schemas
- `DATA_PIPELINE.md` — Datasets, ingestion logic, Bronze/Silver/Gold transformation rules, current Delta tables
- `ML_PIPELINE.md` — 42 features, 3-model ensemble, scoring logic, MLflow experiment plan
- `AGENTS.md` — 19+ agent roles (11 precall + 8+ oncall), tool functions, orchestration flow, state passing
- `VOICE_PIPELINE.md` — Two-call voice system, Pipecat + Sarvam + SmallWebRTC, conversation design
- `ROADMAP.md` — Hour-by-hour execution plan with priority tiers
