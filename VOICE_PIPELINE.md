# VOICE_PIPELINE.md — Real-Time Voice Agent Design & Integration

## Why Voice Matters for This Project

In rural India, literacy rates are ~70% and most farmers don't use apps for financial services. A voice call in Hindi is how they actually receive information. The voice agent isn't a gimmick — it's the access mechanism. The hackathon's Innovation criteria (25%) rewards "a real Indian context in a non-obvious way." Every other team will build a web dashboard. KrishiRin calls the farmer.

---

## Technology Selection Rationale

### Pipecat (Voice Pipeline Framework)
Pipecat is an open-source Python framework for building real-time voice and multimodal conversational agents. Chosen because: (1) First-class Sarvam AI integration — both STT and TTS services are native. (2) Handles STT → LLM → TTS streaming orchestration automatically. (3) Built-in SmallWebRTC transport for browser-based audio. (4) Production-grade — handles frame routing, interruption, and async audio streaming.

### Sarvam STT (Saaras v3)
Chosen over Google Speech-to-Text and Whisper because: (1) Native support for 22 Indian languages with automatic language detection. (2) Code-mixing support — handles Hinglish. (3) Server-side Voice Activity Detection (VAD) with 70ms processing latency. (4) Indian-made model — hackathon bonus.

### Sarvam TTS (Bulbul v3)
Chosen over Google TTS and ElevenLabs because: (1) 25+ Indian voices optimized for natural Hindi speech. (2) Handles ₹2,00,000 as "do lakh rupaye" correctly. (3) Code-switching between Hindi and English sounds natural. (4) WebSocket streaming for low-latency first-chunk delivery. (5) Indian-made model.

**Voice used**: `shubh` — friendly male voice suitable for a loan advisor persona.

### SmallWebRTC (Transport)
Pipecat's built-in SmallWebRTC transport is used instead of Daily.co. Chosen because: (1) No external account needed. (2) Direct browser WebRTC with STUN servers (`stun:stun.l.google.com:19302`). (3) Lower complexity for hackathon demo. (4) SDP offer/answer exchange via `POST /api/offer`.

### OpenAI GPT-4o-mini (LLM)
The voice agent's LLM is OpenAI GPT-4o-mini via the Pipecat `OpenAILLMService`. Chosen for: fast response time, strong instruction following for conversation design, streaming output compatible with Pipecat's frame pipeline, and function calling support for the advisory call's agent trigger mechanism.

---

## Two-Call Voice Architecture

The system conducts TWO separate voice calls with the farmer, each serving a distinct purpose:

### Call 1 — Understanding Call

**Purpose**: Verify farmer details, investigate risk flags, gather context. No loan recommendations.

**System prompt**: Built by `backend/bot_understanding.py:build_understanding_system_prompt(farmer_context)`

**Farmer context injected**:
- Name, grameen_score, risk_category
- District, state, land_holding_acres, crops
- Risk flags from precall analysis
- Auto-generated verification questions

**Conversation design**:
- Hindi/Hinglish, respectful "aap" form
- Ask ONE question at a time
- 2-3 sentences max per response
- Natural verification questions — never reveal flags directly
- Acknowledge farmer's answers warmly
- End with thanks: "Dhanyavaad, aapka din shubh ho!"

**LLM tools**: None. Pure conversational — no function calling.

**Frontend**: Left panel shows PlasmaVisualizer (animated waveform). Right panel shows LiveTranscript (real-time bidirectional dialogue).

**Trigger**: `POST /api/offer` with `call_type: "understanding"`, `farmer_id: "xxx"`
**Completion**: `POST /api/application/{farmer_id}/call1-complete` → advances phase to "processing"

---

### Call 2 — Advisory Call

**Purpose**: Clarify farmer's needs, trigger oncall agent analysis, present personalized loan + crop + cashflow recommendations.

**System prompt**: Built by `backend/bot_advisory.py:build_advisory_system_prompt(farmer_context, results)`

**4-Phase Conversation Flow**:

#### Phase A — Quick Clarification (2 questions)
The LLM asks:
1. "Aapko kitne ka loan chahiye aur kis kaam ke liye?" (How much loan and for what purpose?)
2. "Is baar kaun si fasal ugaane ka plan hai?" (What crops will you plant this season?)

#### Phase B — Trigger Analysis
After getting answers, the LLM calls `trigger_oncall_analysis(summary)`:
- `summary`: Brief text summarizing farmer's responses
- Backend spawns the oncall pipeline (8+ agents) as a background task
- Returns immediately to keep voice conversation flowing

#### Phase C — Brief Wait (~10 seconds)
While agents run in background:
- LLM asks 1-2 casual questions (about farming, family, weather)
- LLM calls `check_analysis_status()` periodically
- Returns: `{ all_done: bool, completed: int, pending: int, message: str }`
- Continues small talk until `all_done=true`

#### Phase D — Present Results
When analysis is complete, LLM calls `get_analysis_results()`:
- Returns: `{ status, policy, agri_plan, cashflow, farmer_summary }`
- LLM presents conversationally:
  - Recommended loan scheme + amount + interest rate
  - Crop plan with expected income
  - Key cashflow points (surplus/deficit months)
  - Next steps to apply at bank

**LLM Function Tools (3)**:

```json
[
  {
    "name": "trigger_oncall_analysis",
    "description": "Triggers background analysis pipeline",
    "parameters": { "summary": "string — farmer response summary" }
  },
  {
    "name": "check_analysis_status",
    "description": "Check if analysis agents have finished",
    "parameters": {}
  },
  {
    "name": "get_analysis_results",
    "description": "Get the final analysis results",
    "parameters": {}
  }
]
```

**Frontend**: Left panel shows PlasmaVisualizer. Right panel shows AgentResultsPanel — real-time agent completion cards with expandable visualizations (charts, tables).

**Trigger**: `POST /api/offer` with `call_type: "advisory"`, `farmer_id: "xxx"`

---

## Voice Pipeline Architecture (Both Calls)

```
FARMER'S MICROPHONE (Browser)
     ↓
SmallWebRTCTransport
  ├── Audio input enabled
  └── Audio output enabled
     ↓
SarvamSTTService
  ├── Model: saaras:v3
  ├── API key: SARVAM_API_KEY
  └── Hindi speech → English text
     ↓
SileroVADAnalyzer
  └── Detects end of farmer's speech
     ↓
LLMUserAggregator
  └── Collects user utterances into context
     ↓
OpenAILLMService
  ├── Model: gpt-4o-mini
  ├── API key: OPENAI_API_KEY
  ├── System prompt: call-type-specific
  ├── [Advisory only] Tools: trigger/check/get analysis
  └── Generates response text (streaming)
     ↓
LLMAssistantAggregator
  └── Collects bot utterances into context
     ↓
SarvamTTSService
  ├── Model: bulbul:v3
  ├── Voice: shubh
  ├── API key: SARVAM_API_KEY
  └── English/Hindi text → Hindi audio (streaming)
     ↓
SmallWebRTCTransport
     ↓
FARMER'S SPEAKER (Browser)
```

**Key implementation detail**: The pipeline is created in `backend/server.py:run_voice_pipeline()`. A new pipeline is instantiated for each call. The Pipecat `Pipeline` chains all processors in order.

---

## Real-time Event Streaming (Advisory Call)

During the advisory call, the backend streams agent completion events to the frontend:

### Backend Side
1. Advisory call registers session: `_active_call_sessions[farmer_id] = session_id`
2. When LLM calls `trigger_oncall_analysis()`, the oncall_runner starts agents
3. As each agent completes, an event is pushed to the session's event queue
4. `GET /api/events/{farmer_id}` (SSE endpoint) reads from this queue and streams to client

### Event Types
```
data: {"type": "waiting"}                          // Waiting for call to start
data: {"type": "agent_update",                     // Agent status change
       "agent": "EligibilityChecker",
       "title": "Finding eligible schemes",
       "icon": "shield",
       "status": "completed",
       "summary": "Found 3 eligible schemes...",
       "result": {...}}
data: {"type": "pipeline_complete"}                // All agents done
data: {"type": "pipeline_error", "error": "..."}   // Pipeline failed
```

### Frontend Side
1. `useAgentEvents(farmerId)` hook subscribes to EventSource
2. Maintains `cards[]` array of AgentCard objects
3. Renders in `AgentResultsPanel`:
   - Each card shows: icon, title, status badge (pending/processing/completed)
   - On click (if completed): expands to show `AgentDetailRenderer`
4. `AgentDetailRenderer` maps result keys to specialized visualizations:
   - `optimal_policy` → LoanPolicyDetail (terms, EMI pie chart, steps)
   - `agri_advisory` → AgriAdvisoryDetail (crop pie chart, revenue bars, sowing table)
   - `cashflow_map` → CashflowDetail (12-month income vs EMI bar chart)
   - `risk_plan` → RiskPlanDetail (risk gauge, mitigation cards)
   - `call_insights` → CallInsightsDetail (acceptance, requirements)
   - `scheme_matches` → SchemeMatchDetail (eligibility table)
   - `bank_products` → BankComparisonDetail (comparison table)

---

## Latency Design

Total end-to-end latency from farmer finishing a sentence to hearing first word of response:

| Stage | Expected | Notes |
|-------|----------|-------|
| Farmer speech → Backend (WebRTC) | ~50ms | SmallWebRTC with STUN |
| Sarvam STT processing | ~70ms | After VAD speech-end detection |
| OpenAI GPT-4o-mini first token | ~500-1500ms | This is the bottleneck |
| Sarvam TTS first audio chunk | ~200ms | Streaming, doesn't wait for full text |
| Audio → Farmer browser (WebRTC) | ~50ms | Return path |
| **Total** | **~900ms - 2s** | Feels natural for conversation |

**Critical insight**: Streaming end-to-end. TTS starts synthesizing as soon as first words arrive from LLM. Farmer hears the response while the LLM is still generating.

**If latency exceeds 3 seconds**: (1) Pre-load ALL farmer context into system prompt — no mid-conversation data fetches. (2) Keep responses under 3 sentences. (3) Function calls (trigger/check/get) return immediately.

---

## Conversation Design Principles

### Both Calls
1. **Language**: Hindi/Hinglish. Respectful "aap" form. Never patronizing.
2. **Length**: Every response under 3 sentences. Voice monologues feel unnatural.
3. **Numbers**: Use concrete ₹ amounts. "₹2 lakh ka loan, ₹6,500 EMI" not "4% per annum."
4. **Specificity**: Advice must reference farmer's actual crops, district, land size — never generic.
5. **Repayment tie-in**: Always connect agricultural advice to loan repayment capacity.
6. **Simplify on confusion**: If farmer seems confused, simplify and repeat, don't add complexity.

### Understanding Call Specific
- Verify flags naturally through questions (don't reveal "we detected a risk")
- Acknowledge answers: "Achha, samajh gaya" before next question
- One question at a time
- No loan recommendations

### Advisory Call Specific
- Phase A: 2 targeted questions only (don't turn into interrogation)
- Phase B: Trigger immediately after getting answers
- Phase C: Casual, warm small talk (weather, crops, family)
- Phase D: Present results conversationally, not as a data dump
- Function calls are invisible to farmer — bot just naturally transitions

---

## Backend Voice Infrastructure

### WebRTC Connection Flow
1. Frontend creates WebRTC offer (SDP)
2. `POST /api/offer` with `{ sdp, type: "offer", call_type, farmer_id }`
3. Backend creates `SmallWebRTCConnection` with STUN config
4. Launches `run_voice_pipeline()` as asyncio background task
5. Returns SDP answer + pc_id
6. WebRTC audio flows bidirectionally

### Session Management
- `pcs_map`: Dict of pc_id → SmallWebRTCConnection (for cleanup)
- `_active_call_sessions`: Dict of farmer_id → session_id (for SSE linking)
- `_sessions`: Dict of session_id → session context (for advisory tools)

### Event Handlers
- `on_client_connected`: Injects system prompt, queues initial message, starts LLM
- `on_client_disconnected`: Cancels pipeline task, cleans up connection

### Function Call Routing (Advisory Only)
When LLM generates a function call:
1. Pipecat intercepts the function call frame
2. Routes to registered handler based on function name
3. Handler calls `bot_advisory.handle_function_call(session_id, fn_name, fn_args)`
4. Handler interfaces with `krishirin_agents.voice_server.oncall_runner`
5. Returns result to LLM, which incorporates it into conversation

---

## Databricks Integration from Voice Agent

### Pre-call Data Loading
Before each voice call, the backend fetches farmer data via `databricks_client.py`:
- `get_farmer_profile(farmer_id)` → from `silver_farmer_profile`
- `get_scored_profile(farmer_id)` → from `scored_profiles`
- `get_loan_strategy(farmer_id)` → from `loan_strategies`
- `get_agri_advisory(farmer_id)` → from `agri_advisory_plans`

All data injected into LLM system prompt. No mid-conversation Delta queries.

### Conversation Logging
`log_conversation_turn(farmer_id, turn_number, speaker, text, call_type)` → INSERT into `conversation_log` table. Happens asynchronously (fire-and-forget) to avoid blocking the voice pipeline.

### Fallback When Databricks Unavailable
Backend checks `db.is_configured`. If false, returns mock/sample data for all endpoints. The entire voice pipeline works without Databricks — just with hardcoded demo data.

---

## Voice Server in krishirin_agents

`krishirin_agents/voice_server/` contains a standalone voice implementation (separate from the backend):

- **server.py**: FastAPI with `POST /api/call/start`, `POST /api/call/process`, `GET /api/events/{session_id}`
- **voice_pipeline.py**: `VoiceSession` class with `stt()`, `process_text()`, `tts()` methods
- **voice_agent_prompt.py**: 4-phase prompt with 5 default clarification questions
- **oncall_runner.py**: Pipeline execution + event streaming for oncall agents
- **models.py**: CallPhase, AgentStatus enums, AGENT_DISPLAY config
- **tools.py**: `trigger_oncall_analysis`, `check_analysis_status`, `get_analysis_results`

The backend (`backend/server.py`) imports from this module for oncall_runner and models.

---

## Setup Checklist

1. **Sarvam AI account**: Get API key from `dashboard.sarvam.ai`. Set `SARVAM_API_KEY` in `.env`.
2. **OpenAI account**: Get API key. Set `OPENAI_API_KEY` in `.env`.
3. **Backend**: `cd backend && pip install -r requirements.txt && uvicorn server:app --host 0.0.0.0 --port 8000`
4. **Frontend**: `cd frontend && npm install && npm run dev` (runs at localhost:3000)
5. **Test**: Open browser → localhost:3000 → navigate to a call page → click "Call Shuru Karein"

**No Daily.co account needed** — SmallWebRTC handles everything via browser-native WebRTC.

---

## Fallback Plan

If the voice pipeline doesn't work during demo:

1. **Pre-recorded demo video**: Record a complete voice conversation with the farmer speaking Hindi and the agent responding.
2. **Text-based testing**: `krishirin_agents/voice_server/` has a text-mode endpoint (`POST /api/call/process`) that bypasses STT/TTS.
3. **Architectural explanation**: Show the Pipecat code, demonstrate STT and TTS work independently. The code and design matter more than a perfect live demo.
