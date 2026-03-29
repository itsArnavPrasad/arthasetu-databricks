# AGENTS.md — Multi-Agent Pipeline Design, Tools & Orchestration

## Framework Choice: Google ADK

Google ADK was chosen over LangGraph and CrewAI for three reasons: (1) Its SequentialAgent and ParallelAgent primitives are purpose-built for our pipeline — agents run in defined order with parallel branches, sharing state via `output_key`, without complex graph definitions. (2) The framework handles state passing between agents automatically — Agent A writes to `output_key="profile"`, and Agent B reads `{profile}` from its instruction template. (3) No explicit state management code needed.

**LLM**: All agents use OpenAI GPT-4o-mini via LiteLLM (`LiteLlm(model="openai/gpt-4o-mini")`). Both `MODEL_FAST` and `MODEL_SMART` in `krishirin_agents/shared/config.py` are configured to use `openai/gpt-4o-mini`.

**Key ADK concepts**:
- **SequentialAgent**: Deterministic orchestrator — runs sub-agents in order, NOT an LLM agent itself. Controls execution order and passes the shared InvocationContext.
- **ParallelAgent**: Runs multiple sub-agents simultaneously and waits for all to complete. Used for independent analysis tasks that don't depend on each other.
- **LlmAgent**: Actual LLM-powered agent that uses GPT-4o-mini for reasoning.
- **State passing**: Each LlmAgent has an `output_key` parameter. When it produces a response, that response is saved to `context.state[output_key]`. Downstream agents read it via `{output_key}` template syntax in their instructions.

---

## Two-Pipeline Architecture

**CRITICAL WORKFLOW ORDER**: ML scoring runs FIRST as a separate Databricks notebook → populates `scored_profiles` Delta table → THEN the agent pipelines begin.

The system has TWO distinct agent pipelines:

1. **Precall Pipeline** (11 agents, 6 stages): Runs BEFORE voice calls. Analyzes farmer data, computes eligibility, identifies gaps, designs loan strategy, builds agricultural advisory. Triggered by `POST /api/application/{farmer_id}/analyze`.

2. **Oncall Pipeline** (8+ agents, 3 stages): Runs DURING the advisory voice call. Triggered by the voice LLM calling `trigger_oncall_analysis()`. Analyzes call transcript, optimizes loan policy based on farmer's stated needs, builds detailed crop plan, creates risk mitigation strategy, maps 12-month cashflow.

The split is intentional: Precall does broad analysis with all available data. Oncall refines that analysis using the farmer's actual responses from the voice conversation.

---

## Precall Pipeline — 11 Agents, 6 Stages

**Location**: `krishirin_agents/precall/`
**Root agent**: `krishirin_agents/precall/coordinator/agent.py` → `root_agent` (SequentialAgent)

```
root_agent (SequentialAgent)
│
├── Stage 1: data_loader_agent
│   Loads all farmer data into state
│   Output key: farmer_context
│
├── Stage 2: parallel_analysis (ParallelAgent — 6 agents simultaneously)
│   ├── score_explainer_agent      → credit_assessment
│   ├── risk_flag_detector_agent   → risk_flags
│   ├── market_research_agent      → market_research
│   ├── scheme_rag_agent           → scheme_rag_results
│   ├── scheme_web_agent           → scheme_web_results
│   └── eligibility_evaluator_agent → eligibility_evaluation
│
├── Stage 3: scheme_synthesizer_agent
│   Merges 3 scheme sources into unified report
│   Output key: eligibility_report
│
├── Stage 4: gap_analyzer_agent
│   Identifies gaps, warnings, improvement suggestions
│   Output key: gap_analysis
│
├── Stage 5: loan_strategy_agent
│   Designs optimal loan package
│   Output key: loan_strategy
│
└── Stage 6: precall_synthesis_agent
    Final synthesis + write to Delta
    Output key: precall_analysis
```

---

### Stage 1: Data Loader Agent

**Location**: `krishirin_agents/precall/data_loader/`
**Model**: GPT-4o-mini
**Output key**: `farmer_context`

**Role**: Load all farmer data from Delta tables (or sample data when Databricks is unavailable) into a unified context object.

**Tools (6)**:
| Tool | Source | What it returns |
|------|--------|----------------|
| `load_farmer_profile` | `krishirin.loan_advisory.silver_farmer_profile` | Name, district, state, land, crops, existing loans, schemes, bank summary |
| `load_ml_scores` | `krishirin.loan_advisory.scored_profiles` | Grameen score, risk category, repayment prob, risk cluster, predicted capacity, positive/negative factors |
| `load_district_data` | `krishirin.loan_advisory.silver_district_features` | Avg yield, irrigation %, rainfall, crop failure rate, dominant crops, soil type |
| `load_crop_calendar` | `krishirin.loan_advisory.silver_crop_calendar` | Sowing/harvest windows, seed rates, fertilizer, water requirements per crop per zone |
| `load_msp_prices` | `krishirin.loan_advisory.bronze_msp_prices` | MSP per quintal for 22 crops |
| `fetch_weather_data` | OpenWeatherMap API | Current conditions + 7-day forecast for farmer's district |

**Data models** (Pydantic, in `data_loader/models.py`): FarmerProfile, MLScores, DistrictData, CropCalendar, MSPPrices, WeatherData.

**Fallback**: When `USE_SAMPLE_DATA=True` (Databricks not configured), returns hardcoded data for Ramesh Patil, Nashik — 3 acres, soybean/onion/wheat, Grameen Score 68.5, Category B.

---

### Stage 2: Parallel Analysis (6 Agents)

All 6 agents run simultaneously via **ParallelAgent**. Each reads `{farmer_context}` from state.

#### 2a. Score Explainer Agent

**Location**: `krishirin_agents/precall/score_explainer/`
**Model**: GPT-4o-mini
**Input**: `{farmer_context}` (includes ML scores)
**Output key**: `credit_assessment`
**Tools**: None (reads from farmer_context)

**Role**: Translate the ML Grameen Score into plain language. Explains WHY the score is what it is — references alternative data signals (savings habits, scheme participation, seasonal patterns), compares to district benchmarks, identifies top strengths and risks, suggests concrete improvement actions. Keeps language simple for eventual Hindi voice delivery.

**Output format**: Grameen score, risk category, 5-line explanation, top 3 strengths, top 3 risks, 2 improvement actions, district comparison.

#### 2b. Risk Flag Detector Agent

**Location**: `krishirin_agents/precall/risk_flag_detector/`
**Model**: GPT-4o-mini
**Input**: `{farmer_context}`
**Output key**: `risk_flags`
**Tools**: None

**Role**: Detect red flags across multiple categories — financial risks (high DTI, existing defaults, low savings), agricultural risks (mono-cropping, rainfed in drought zone, pest-prone region), documentation risks (missing land records, bank history gaps), scheme compliance risks (PM-KISAN enrollment gaps). Each flag includes type (critical/warning/info), category, description, and detail.

#### 2c. Market Research Agent

**Location**: `krishirin_agents/precall/market_research/`
**Model**: GPT-4o-mini
**Input**: `{farmer_context}`
**Output key**: `market_research`
**Tools**: None

**Role**: Generate market intelligence — current mandi prices for farmer's crops, disease/pest alerts relevant to region and season, weather advisory implications, government scheme updates, market timing recommendations.

#### 2d. Scheme RAG Agent

**Location**: `krishirin_agents/precall/scheme_matching/subagents/scheme_rag/`
**Model**: GPT-4o-mini
**Input**: `{farmer_context}`
**Output key**: `scheme_rag_results`
**Tools**:
| Tool | Description |
|------|-------------|
| `faiss_search` | Searches FAISS vector index of scheme documents. Runs 4 queries with top_k=5. Uses all-MiniLM-L6-v2 embeddings (22MB, CPU-friendly). Returns scheme_name, text chunk, source, similarity score. |

**Role**: Search the FAISS index of government scheme PDFs (KCC guidelines, PMFBY rules, PM-KISAN, MUDRA, state schemes) to find relevant eligibility criteria and benefits for this specific farmer.

#### 2e. Scheme Web Agent

**Location**: `krishirin_agents/precall/scheme_matching/subagents/scheme_web/`
**Model**: GPT-4o-mini
**Input**: `{farmer_context}`
**Output key**: `scheme_web_results`
**Tools**: None (knowledge-based)

**Role**: Provide latest scheme updates and changes from the agent's training knowledge. Supplements the RAG results with more recent information about scheme modifications, new announcements, or regional variations.

#### 2f. Eligibility Evaluator Agent

**Location**: `krishirin_agents/precall/scheme_matching/subagents/eligibility_evaluator/`
**Model**: GPT-4o-mini
**Input**: `{farmer_context}`
**Output key**: `eligibility_evaluation`
**Tools**: None (rule-based reasoning via prompt)

**Role**: Evaluate eligibility against specific scheme rules:
- **KCC**: Collateral waived up to ₹1.6L. Interest 7% with 2% govt subvention + 3% prompt repayment incentive = 4% effective for ≤₹3L.
- **PM-KISAN**: ₹6,000/year in 3 installments for land-owning farmers.
- **PMFBY**: Premium 2% Kharif, 1.5% Rabi. Covers notified crops in notified areas.
- **MUDRA**: Shishu (up to ₹50K), Kishore (₹50K-5L), Tarun (₹5L-10L).
- **State-specific schemes**: Based on farmer's state.

---

### Stage 3: Scheme Synthesizer Agent

**Location**: `krishirin_agents/precall/scheme_matching/synthesizer.py`
**Model**: GPT-4o-mini
**Input**: `{scheme_rag_results}`, `{scheme_web_results}`, `{eligibility_evaluation}`
**Output key**: `eligibility_report`
**Tools**: None

**Role**: Merge all three scheme analysis sources (RAG, web, rule-based) into a single unified eligibility report. Resolves conflicts, ranks schemes by fit, produces a final list with: scheme name, eligibility (bool), match percentage, benefit amount, missing requirements, and details.

---

### Stage 4: Gap Analyzer Agent

**Location**: `krishirin_agents/precall/gap_analyzer/`
**Model**: GPT-4o-mini
**Input**: `{farmer_context}`, `{eligibility_report}`
**Output key**: `gap_analysis`

**Tools**:
| Tool | Description |
|------|-------------|
| `profile_validator` | Rule-based checker (not LLM). Validates: required documents present? Bank history ≥6 months? Aadhaar linked? DTI ratio above threshold? Existing defaults? Data inconsistencies? Returns structured validation report. |

**Output format** (defined in `gap_analyzer/models.py`):
- `critical_gaps`: Blocking issues preventing loan approval
- `warnings`: Issues that weaken but don't block the application
- `improvement_suggestions`: Actionable steps to strengthen the application
- `application_ready`: Boolean
- `readiness_score`: 0-100

---

### Stage 5: Loan Strategy Agent

**Location**: `krishirin_agents/precall/loan_strategy/`
**Model**: GPT-4o-mini
**Input**: All previous state (farmer_context, credit_assessment, eligibility_report, gap_analysis)
**Output key**: `loan_strategy`

**Tools**:
| Tool | Description |
|------|-------------|
| `interest_calculator` | Computes EMI, total repayment, and total interest. Applies interest rate rules (7% base, 2% govt subvention for ≤₹3L, 3% prompt repayment incentive). |
| `collateral_checker` | Determines collateral requirements per RBI KCC guidelines. Waived up to ₹1.6L, hypothecation up to ₹3L, mortgage above ₹3L. |

**Output format**: Recommended product (KCC/MUDRA/Term Loan), amount, tenure, interest rate (nominal and effective), EMI, total repayment, collateral details, harvest-aligned repayment schedule (Kharif: Nov-Dec, Rabi: Apr-May), rationale, alternative option.

**Key rule**: Repayment MUST align with crop harvesting. Never schedule large repayments during lean season (Jun-Aug).

---

### Stage 6: Precall Synthesis Agent

**Location**: `krishirin_agents/precall/precall_synthesis/`
**Model**: GPT-4o-mini
**Input**: ALL previous state
**Output key**: `precall_analysis`

**Tools**:
| Tool | Description |
|------|-------------|
| `write_analysis_to_delta` | Writes the complete precall analysis to `krishirin.loan_advisory.precall_analysis` Delta table. |

**Role**: Create the final synthesis — executive summary, voice agent briefing document (what the bot should know before the call), auto-generated verification questions for Call 1, and the complete analysis package. This is the final output that both the dashboard and voice agent consume.

---

## Oncall Pipeline — 8+ Agents, 3 Stages

**Location**: `krishirin_agents/oncall/`
**Root agent**: `krishirin_agents/oncall/coordinator/agent.py` → `postcall_advisory_pipeline` (SequentialAgent)
**Triggered by**: Voice LLM calling `trigger_oncall_analysis()` during the advisory call

```
postcall_advisory_pipeline (SequentialAgent)
│
├── Stage 1: call_analyzer_agent
│   Extracts insights from call transcript
│   Output key: call_insights
│
├── Stage 2: parallel_tracks (ParallelAgent — 3 independent tracks)
│   │
│   ├─ Track A: loan_policy_pipeline (SequentialAgent)
│   │  ├── parallel_policy_search (ParallelAgent)
│   │  │  ├── scheme_matcher_agent   → state
│   │  │  └── bank_product_agent     → state
│   │  └── policy_optimizer_agent    → optimal_policy
│   │
│   ├─ Track B: agri_advisory_pipeline (SequentialAgent)
│   │  ├── crop_planner_agent                     → crop_plan
│   │  ├── parallel_after_crop (ParallelAgent)
│   │  │  ├── input_cost_agent                    → state
│   │  │  └── market_timing_agent                 → state
│   │  └── agri_synthesizer_agent                 → agri_advisory
│   │
│   └─ Track C: risk_mitigator_agent              → risk_plan
│
└── Stage 3: cashflow_mapper_agent
    Input: All above outputs
    Output key: cashflow_map
```

---

### Stage 1: Call Analyzer Agent

**Location**: `krishirin_agents/oncall/call_analyzer/`
**Model**: GPT-4o-mini
**Input**: Call transcript + precall context
**Output key**: `call_insights`

**Output format** (defined in `call_analyzer/models.py`):
- `stated_requirement`: What the farmer said they need (amount, purpose)
- `concerns`: Farmer's worries or objections
- `acceptance_status`: How receptive the farmer is to the loan
- `preferred_crops`: What they plan to grow this season
- Additional context from the conversation

---

### Stage 2: Three Parallel Tracks

#### Track A: Loan Policy Pipeline

**Location**: `krishirin_agents/oncall/loan_policy/`

Three agents in sequence, with the first two running in parallel:

1. **scheme_matcher_agent**: Re-evaluates scheme matching using call insights (farmer's stated needs may differ from profile data)
2. **bank_product_agent**: Compares loan products across banks (interest rates, fees, processing time)
3. **policy_optimizer_agent**: Selects best scheme + bank combination, optimizes terms → **output_key: `optimal_policy`**

#### Track B: Agricultural Advisory Pipeline

**Location**: `krishirin_agents/oncall/agri_advisory/`

Four agents with mixed sequential/parallel execution:

1. **crop_planner_agent** (`krishirin_agents/oncall/agri_advisory/subagents/crop_planner/`):
   - Creates sowing plan: crop, area allocation, season, sowing window, expected yield, expected revenue
   - Output key: `crop_plan`

2. **input_cost_agent** (`krishirin_agents/oncall/agri_advisory/subagents/input_cost/`):
   - Estimates cultivation costs per crop (seeds, fertilizer, pesticide, labor, irrigation)
   - Identifies cost reduction opportunities
   - Runs in PARALLEL with market_timing after crop_plan is ready

3. **market_timing_agent** (`krishirin_agents/oncall/agri_advisory/subagents/market_timing/`):
   - Weather-aware timing guidance, selling strategy per crop, MSP procurement windows
   - Runs in PARALLEL with input_cost after crop_plan is ready

4. **agri_synthesizer_agent**:
   - Merges crop plan, costs, and market timing into comprehensive advisory
   - Adds income diversification recommendations (dairy, poultry, kitchen garden, MGNREGA, value addition)
   - Output key: `agri_advisory`

**agri_advisory output**: land_assessment, sowing_plan (array), input_cost_guidance, weather_guidance, market_timing, income_diversification, repayment_cashflow_map (array).

#### Track C: Risk Mitigator Agent

**Location**: `krishirin_agents/oncall/risk_mitigator/`
**Model**: GPT-4o-mini
**Input**: `{risk_flags}`, `{call_insights}`
**Output key**: `risk_plan`

**Role**: Build a risk mitigation plan — crop insurance recommendations (PMFBY), income diversification strategies, savings buffer sizing, documentation remediation plan. Prioritizes actions by urgency.

---

### Stage 3: Cashflow Mapper Agent

**Location**: `krishirin_agents/oncall/cashflow_mapper/`
**Model**: GPT-4o-mini
**Input**: All above outputs (optimal_policy, agri_advisory, risk_plan, farmer_context)
**Output key**: `cashflow_map`

**Role**: THE BRIDGE between agricultural advisory and loan repayment. Produces a 12-month month-by-month projection:
- Per month: income sources (crop sales, dairy, MGNREGA, PM-KISAN), total income, EMI due, surplus/deficit
- Identifies surplus months (post-harvest) for lump-sum repayments
- Identifies deficit months (lean season) and how allied income covers them
- Sizes the buffer needed for lean months
- Maps exactly when each crop sale covers which loan installment

---

## Voice Agent Integration

The voice agent is NOT a Google ADK agent. It runs via Pipecat on the local machine.

### Two-Call System

**Call 1 — Understanding Call** (`backend/bot_understanding.py`):
- System prompt built from: farmer name, grameen score, risk category, district, land, crops, flags, auto-generated verification questions
- Bot verifies risky flags naturally through conversation (doesn't reveal flags)
- Hindi/Hinglish, respectful "aap" form, 2-3 sentences max per response
- NO loan recommendations — purely investigative
- LLM: OpenAI GPT-4o-mini, no function tools

**Call 2 — Advisory Call** (`backend/bot_advisory.py`):
- 4-phase conversation flow with LLM function calling:
  - **Phase A (Clarification)**: Ask 2 questions — "Kitne ka loan chahiye, kis kaam ke liye?" and "Kaun si fasal ugaane ka plan hai?"
  - **Phase B (Trigger)**: LLM calls `trigger_oncall_analysis(summary)` → spawns oncall pipeline in background
  - **Phase C (Small Talk)**: Ask casual questions while agents run (~10s). LLM calls `check_analysis_status()` to poll.
  - **Phase D (Results)**: LLM calls `get_analysis_results()` → presents loan scheme, crop plan, cashflow conversationally

**Function tools registered on the LLM**:
| Function | Purpose | Returns |
|----------|---------|---------|
| `trigger_oncall_analysis(summary)` | Fire oncall pipeline in background | Immediate confirmation |
| `check_analysis_status()` | Poll agent completion | `{all_done, completed, pending, message}` |
| `get_analysis_results()` | Fetch final outputs | `{policy, agri_plan, cashflow, farmer_summary}` |

### Real-time Event Streaming

During the advisory call, the backend streams agent completion events to the frontend via SSE (`GET /api/events/{farmer_id}`):
- `agent_update`: Agent name, title, icon, status (pending/processing/completed), summary, result data
- `pipeline_complete`: All agents finished
- `pipeline_error`: Pipeline failed

The frontend's `AgentResultsPanel` renders these as expandable cards with detailed visualizations (charts, tables).

---

## Complete State Keys Reference

| State Key | Set By | Read By | Contains |
|-----------|--------|---------|----------|
| `farmer_context` | data_loader | All downstream | Complete farmer data (profile, ML scores, district, weather, crops, MSP) |
| `credit_assessment` | score_explainer | gap_analyzer, loan_strategy, synthesis | Plain-language score explanation, strengths, risks |
| `risk_flags` | risk_flag_detector | gap_analyzer, risk_mitigator, synthesis | Categorized risk flags (critical/warning/info) |
| `market_research` | market_research | synthesis | Mandi prices, disease alerts, scheme updates |
| `scheme_rag_results` | scheme_rag | scheme_synthesizer | FAISS search results from scheme documents |
| `scheme_web_results` | scheme_web | scheme_synthesizer | Knowledge-based scheme updates |
| `eligibility_evaluation` | eligibility_evaluator | scheme_synthesizer | Rule-based eligibility per scheme |
| `eligibility_report` | scheme_synthesizer | gap_analyzer, loan_strategy, synthesis | Unified scheme eligibility report |
| `gap_analysis` | gap_analyzer | loan_strategy, synthesis | Gaps, warnings, suggestions, readiness |
| `loan_strategy` | loan_strategy | synthesis, voice agent | Complete loan package recommendation |
| `precall_analysis` | precall_synthesis | Voice agent (both calls) | Final synthesis + voice briefing |
| `call_insights` | call_analyzer | All oncall downstream | Farmer's stated needs from call transcript |
| `crop_plan` | crop_planner | input_cost, market_timing, agri_synthesizer | Sowing plan with area/yield/revenue |
| `agri_advisory` | agri_synthesizer | cashflow_mapper, voice agent | Complete agricultural advisory |
| `optimal_policy` | policy_optimizer | cashflow_mapper, voice agent | Best loan product + bank + terms |
| `risk_plan` | risk_mitigator | cashflow_mapper, voice agent | Insurance, diversification, buffers |
| `cashflow_map` | cashflow_mapper | voice agent | 12-month income vs EMI projection |

---

## Shared Infrastructure

### Config (`krishirin_agents/shared/config.py`)
```python
MODEL_FAST = LiteLlm(model="openai/gpt-4o-mini")
MODEL_SMART = LiteLlm(model="openai/gpt-4o-mini")
```
Also defines: DATABRICKS_HOST/TOKEN/HTTP_PATH, USE_SAMPLE_DATA flag, FAISS_INDEX_PATH, FAISS_CHUNKS_PATH, and all Delta table names.

### Delta Client (`krishirin_agents/shared/delta_client.py`)
Functions: `get_connection()`, `query_one(sql)`, `query_all(sql)`, `execute_write(sql)`.

### Weather Client (`krishirin_agents/shared/weather_client.py`)
`fetch_weather(district)` → current conditions + 7-day forecast. Maps 20+ Indian districts to (lat, lon). Uses OpenWeatherMap free tier.

### FAISS Client (`krishirin_agents/shared/faiss_client.py`)
`search(query, top_k=5)` → loads sentence-transformers all-MiniLM-L6-v2, searches FAISS index of scheme document chunks. Returns scheme_name, text, source, score.

### Sample Data (`krishirin_agents/shared/sample_data.py`)
Hardcoded test farmer: Ramesh Patil, 42, Nashik, 3 acres owned, mixed irrigation. Soybean/onion/wheat. Grameen Score 68.5 (Category B). Repayment prob 0.78. Predicted capacity ₹2,00,000. Includes district data, crop calendar, MSP prices, weather mock.

---

## Orchestration Decisions

**Why two pipelines (precall + oncall)**: Precall runs broad analysis with available data — it doesn't know what the farmer actually wants. Oncall refines after hearing the farmer's voice: their actual loan need, preferred crops, concerns. The oncall pipeline personalizes the recommendation using real conversation context.

**Why ParallelAgent in Stage 2**: Score explanation, risk detection, market research, and scheme matching are all independent analyses of the same farmer data. Running 6 agents in parallel cuts latency from ~30s sequential to ~5s parallel.

**Why 3 parallel tracks in oncall**: Loan policy optimization, agricultural advisory, and risk mitigation are independent domains that don't depend on each other — only on the call insights. Running them in parallel keeps the farmer waiting ~10s instead of ~30s during the advisory call.

**Why ML is NOT inside any agent**: (1) Spark MLlib requires PySpark context — ADK agents run separately. (2) ML scoring should be batch-capable (score 1000 farmers at once). (3) Separation means ML is independently testable. Agents read from `scored_profiles`, never invoke models.

**Error handling**: Each agent validates its inputs (checks state keys exist). If `scored_profiles` has no row for the farmer_id, the data_loader returns an explicit error. `USE_SAMPLE_DATA` provides a graceful offline fallback.
