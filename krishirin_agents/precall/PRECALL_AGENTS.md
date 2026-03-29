# KrishiRin Pre-Call Analysis — Multi-Agent Pipeline

## What It Does

Takes a farmer's profile + pre-computed ML scores and produces a complete credit advisory report before the voice call. Built on **Google ADK** with **OpenAI gpt-4o-mini / gpt-4o** via LiteLLM. Runs as a standalone app, connects to Databricks Delta via SQL connector.

---

## Pipeline Architecture

```
coordinator (SequentialAgent) ← select this in ADK web
│
├── Stage 1: data_loader_agent
│   Loads all farmer data into state (single source of truth)
│
├── Stage 2: parallel_analysis (ParallelAgent)
│   Runs 3 agents simultaneously:
│   ├── score_explainer_agent    → credit_assessment
│   ├── risk_flag_detector_agent → risk_flags
│   └── market_research_agent    → market_research
│
├── Stage 3: scheme_matching_pipeline (SequentialAgent)
│   ├── parallel_scheme_search (ParallelAgent)
│   │   Runs 3 agents simultaneously:
│   │   ├── scheme_rag_agent            → scheme_rag_results
│   │   ├── scheme_web_agent            → scheme_web_results
│   │   └── eligibility_evaluator_agent → eligibility_evaluation
│   └── scheme_synthesizer_agent        → eligibility_report
│
├── Stage 4: gap_analyzer_agent    → gap_analysis
├── Stage 5: loan_strategy_agent   → loan_strategy
└── Stage 6: precall_synthesis_agent → precall_analysis (final output)
```

**11 agents total** | **6 sequential stages** | **2 parallel stages** (Stages 2 and 3a)

---

## Data Inputs

| Source | Data | Loaded By |
|--------|------|-----------|
| `silver_farmer_profile` (Delta) | Name, age, district, land, crops, loans, bank summary, documents | `load_farmer_profile` tool |
| `scored_profiles` (Delta) | Grameen Score (0-100), risk category (A-D), repayment probability, predicted loan capacity, top positive/negative factors | `load_ml_scores` tool |
| `silver_district_features` (Delta) | District avg yields, irrigation %, rainfall, crop failure rate, soil type | `load_district_data` tool |
| `silver_crop_calendar` (Delta) | Sowing/harvest windows per crop and season | `load_crop_calendar` tool |
| `bronze_msp_prices` (Delta) | MSP prices for 22 crops | `load_msp_prices` tool |
| OpenWeatherMap API | Current weather + 7-day forecast for farmer's district | `fetch_weather_data` tool |
| FAISS index | Pre-indexed government scheme PDFs (KCC, PM-KISAN, PMFBY, MUDRA) | `faiss_search` tool |

All data is loaded in **Stage 1** and stored in `state["farmer_context"]`. No downstream agent queries Delta directly.

When Databricks is not connected, the pipeline falls back to built-in sample data (Ramesh Patil, Nashik, 3 acres, soybean/onion/wheat, Grameen Score 68.5/B).

---

## What Each Agent Does

### Stage 1 — Data Loader (gpt-4o-mini)
Calls 6 tool functions to load farmer profile, ML scores, district data, crop calendar, MSP prices, and weather. Assembles everything into a single `farmer_context` JSON.

### Stage 2 — Parallel Analysis (3 agents, gpt-4o-mini)

| Agent | Purpose | Output |
|-------|---------|--------|
| **Score Explainer** | Translates ML scores into plain-language explanation. Top 3 strengths, top 3 risks, 2 improvement actions, district comparison. Language kept simple for Hindi translation. | `credit_assessment` |
| **Risk Flag Detector** | Scans for red flags: high DTI, irregular income, no savings, defaults, single-crop dependency, rainfed vulnerability, missing insurance, missing documents. Each flag has specific numbers. | `risk_flags` |
| **Market Research** | Provides current mandi prices for farmer's crops, disease/pest alerts, weather advisory, recent scheme announcements. | `market_research` |

### Stage 3 — Scheme Matching (3 parallel + 1 synthesizer)

| Agent | Purpose | Output |
|-------|---------|--------|
| **Scheme RAG** (gpt-4o-mini) | Generates 4 queries from farmer profile, searches FAISS index of scheme PDFs, retrieves relevant chunks. | `scheme_rag_results` |
| **Scheme Web** (gpt-4o-mini) | Provides latest scheme updates, changed eligibility criteria, state-specific schemes. | `scheme_web_results` |
| **Eligibility Evaluator** (gpt-4o-mini) | Evaluates farmer against KCC, PM-KISAN, PMFBY, MUDRA, and state scheme rules. Calculates match %, lists missing criteria. | `eligibility_evaluation` |
| **Scheme Synthesizer** (gpt-4o) | Merges all 3 sources into unified eligibility report. Picks recommended primary scheme. | `eligibility_report` |

### Stage 4 — Gap Analyzer (gpt-4o-mini)
Combines rule-based validation (via `profile_validator` tool) with AI analysis. Identifies:
- **Critical gaps** — blocking issues (missing land record, high DTI, existing default)
- **Warnings** — weakening issues (income mismatch, no insurance)
- **Suggestions** — strengthening steps (enroll in PM-KISAN, diversify crops)

Produces a `readiness_score` (0-100) and `application_ready` boolean.

### Stage 5 — Loan Strategy (gpt-4o)
Designs the optimal loan package using `interest_calculator` and `collateral_checker` tools:
- Selects product (KCC / MUDRA / Term Loan)
- Calculates effective interest rate (4% for KCC ≤ ₹3L after subvention)
- Checks collateral requirements (waived up to ₹1.6L)
- Builds harvest-aligned repayment schedule (pay after Kharif Nov-Dec, Rabi Apr-May — never in lean Jun-Aug)

### Stage 6 — Pre-Call Synthesis (gpt-4o)
Combines all outputs into the final report:
- **Executive summary** — 5-sentence recommendation for bank operator
- **Voice agent briefing** — condensed version (under 500 words, simple language, Hindi-translatable) that gets injected into the voice agent's system prompt

Writes the result to `precall_analysis` Delta table.

---

## Final Output Structure

```
precall_analysis
├── farmer_id
├── generated_at
├── score_summary        ← from Stage 2 (score explainer)
├── risk_flags           ← from Stage 2 (risk detector)
├── market_insights      ← from Stage 2 (market research)
├── eligible_schemes     ← from Stage 3 (scheme matching)
├── gaps_to_fix          ← from Stage 4 (gap analyzer)
├── loan_strategy        ← from Stage 5 (loan strategy)
├── executive_summary    ← 5-sentence bank operator recommendation
└── voice_agent_briefing ← condensed briefing for Hindi voice call
```

---

## State Flow

```
Input: "Run analysis for farmer FARMER_001"
         │
Stage 1  │  data_loader calls 6 tools
         ▼
    state["farmer_context"]
         │
Stage 2  │  3 agents run in PARALLEL
         ├──→ state["credit_assessment"]
         ├──→ state["risk_flags"]
         └──→ state["market_research"]
         │
Stage 3  │  3 agents run in PARALLEL, then 1 synthesizer
         ├──→ state["scheme_rag_results"]
         ├──→ state["scheme_web_results"]
         ├──→ state["eligibility_evaluation"]
         └──→ state["eligibility_report"]  (merged)
         │
Stage 4  ▼
    state["gap_analysis"]
         │
Stage 5  ▼
    state["loan_strategy"]
         │
Stage 6  ▼
    state["precall_analysis"]  ← FINAL OUTPUT (also written to Delta)
```

---

## How to Run

```bash
cd "Databricks Hack"
adk web krishirin_agents
```

1. Open `http://127.0.0.1:8000`
2. Select **coordinator** from the app dropdown
3. Type: `Run complete pre-call analysis for farmer FARMER_001`

---

## Model Usage

| Model | Cost | Used By |
|-------|------|---------|
| gpt-4o-mini | ~$0.15/M input tokens | 8 agents — data loader, score explainer, risk flags, market research, scheme RAG, scheme web, eligibility evaluator, gap analyzer |
| gpt-4o | ~$2.50/M input tokens | 3 agents — scheme synthesizer, loan strategy, pre-call synthesis |

Estimated cost per farmer: **< $0.02**
Estimated latency: **~15 seconds** (parallel stages save ~6s vs sequential)
