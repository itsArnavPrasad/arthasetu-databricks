# ROADMAP.md — Execution Plan, Priorities & Decision Points

## Priority Framework

**P0 (Must Ship)**: The project doesn't demo without these. Build first, verify early, don't optimize prematurely.
**P1 (Should Ship)**: Significantly improves the demo and score. Build after P0 is complete and working.
**P2 (Bonus)**: Polish, edge cases, and bonus point features. Only if time remains after P1.

The single most important principle: **get end-to-end working early, then improve.** A rough but complete pipeline beats a polished but incomplete one. Judges can't score what they can't see.

---

## Pre-Hackathon (Night Before)

### Goal: Walk in with zero unknowns. Every account created, every dataset downloaded, every library tested.

**Accounts to create** (P0):
- Databricks Free Edition — both members, one shared workspace
- Sarvam AI — both members (₹2,000 total free credits)
- Google AI Studio — Gemini API key
- Daily.co — free tier, API key
- Kaggle — for Home Credit dataset download

**Datasets to download** (P0):
- Home Credit Default Risk from Kaggle (~2.7GB, 4 CSV files minimum)
- ICRISAT District-Level Database (Excel files for crop, rainfall, irrigation, land holdings)
- MSP prices compiled into a simple 22-row CSV
- Government scheme documents converted to plain text for RAG

**Local tests to run** (P1 — saves hours on Day 1):
- Sarvam STT: Upload a short Hindi audio clip to the REST API, verify transcription works
- Sarvam TTS: Send Hindi text, verify you get audio back
- Pipecat: Run the minimal "hello world" example from Sarvam's docs, verify end-to-end audio works
- Databricks SQL connector: Connect from your laptop to the workspace, run a simple query

**Documentation to prepare** (P1):
- Review all .md files — both team members should understand the full architecture
- Draft the GitHub README skeleton
- Draft the architecture diagram (can use Mermaid, draw.io, or even hand-drawn)

---

## Day 1: 11:00 AM – 6:00 PM

### 11:00 AM – 12:30 PM | Setup Sprint (Both Members Together)

**Goal**: Databricks workspace fully operational with all reference data loaded.

This is pure setup — no creative work, no decisions. Just execute the checklist:

1. Install all Python packages in the Databricks notebook (pip install command)
2. Create the catalog and schema (`krishirin.loan_advisory`)
3. Store API keys as Databricks secrets (or environment variables if secrets aren't available on Free Edition)
4. Upload dataset CSV files to Databricks Volumes or DBFS
5. Run Bronze ingestion — load all CSVs into Delta tables
6. Verify with COUNT queries: Home Credit should have ~307K rows, MSP should have 22 rows

**Checkpoint at 12:30**: Every Bronze table exists and has data. If this isn't done, nothing else can proceed.

**Decision point**: If ICRISAT Excel files are hard to parse in Spark, skip them for now — use the Kaggle Indian Agriculture dataset as a simpler alternative. Don't spend more than 30 minutes on data format issues.

---

### 12:30 PM – 2:30 PM | Parallel Build (Split Tasks)

This is where the two team members diverge. Work independently but sync every 45 minutes.

**Person A: Data Pipeline + ML Foundation**

Goal: Get from Bronze to Gold tables with ML-ready features.

1. Build Silver transformation — clean Home Credit data, select relevant columns, compute derived ratios. Handle nulls via median imputation. Write to `silver_home_credit_features`.
2. Build district features table — if ICRISAT data is loaded, aggregate to district-level summaries. If not, create a minimal district lookup table from available data.
3. Generate synthetic farmer profiles — 5,000 farmers with realistic Indian agricultural parameters. Include 12 months of transaction data per farmer. Write to `silver_farmer_profile` and `silver_transactions`.
4. Build Gold feature engineering — compute all 42 features using PySpark. Write to `gold_credit_features`. Create train/test splits.

**Checkpoint at 2:30**: The `gold_credit_features` table exists with 42+ columns and thousands of rows. Ready for ML training.

**Decision point for Person A**: If computing all 42 features takes too long, prioritize the top 20 most impactful features (income features 1-12, DTI ratio, savings rate, land holding, and repayment history). A model with 20 good features beats one with 42 buggy features.

**Person B: Agent Framework + Voice Pipeline Start**

Goal: Get Google ADK agents working with Gemini, and Pipecat voice bot running locally.

1. Install Google ADK in the Databricks notebook. Create a test LlmAgent with Gemini 2.0 Flash. Verify it responds correctly.
2. Define Agent 1 (DocParser) with its system prompt and a stub tool function. Test with sample document text.
3. Define Agent 2 (EligibilityChecker) with its prompt. Use a stub for the FAISS tool (just return hardcoded scheme data for now).
4. Define Agents 3-5 with prompts and stub tools. Agent 3's stub tool (`delta_score_reader`) should return hardcoded score data for now (e.g., grameen_score=72, risk_category="B"). Later during integration, this stub gets replaced with a real Delta table read from `scored_profiles` — but it should NEVER invoke an ML model directly.
5. Create the SequentialAgent orchestrator connecting all 5 agents. Test end-to-end with a sample farmer.
6. On the local machine: Get Pipecat + Sarvam + Daily.co working. Just echo back what the user says for now.

**Checkpoint at 2:30**: The 5-agent pipeline runs end-to-end (even with stub tools). The voice bot responds in Hindi (even if just echoing).

**Decision point for Person B**: If Google ADK installation fails or is incompatible with the Databricks runtime, fall back to a simple sequential function chain — define each agent as a Python function that calls Gemini API via the `google-generativeai` SDK, passing state as a dictionary between functions. The agent abstraction is nice but not required.

---

### 2:30 PM – 4:30 PM | ML Training + Full Integration

**Person A: ML Training**

Goal: Train 6 MLflow experiments, register the best model, run batch scoring.

1. Build the ML training notebook with MLflow tracking.
2. Run experiments 1-6 (Logistic Regression, Random Forest, GBT × 3, GBT + feature selection).
3. Compare results in MLflow. Register the best model.
4. Build the KMeans clustering model (separate MLflow experiment).
5. Build the RF Regressor for loan capacity (separate MLflow experiment).
6. Build the Grameen Composite Scorer — combine all three model outputs.
7. Run batch scoring on all farmers. Write to `scored_profiles` table.

**Checkpoint at 4:30**: `scored_profiles` table has a grameen_score for every farmer. MLflow shows 6+ experiment runs.

**Decision point**: If Spark MLlib GBTClassifier is problematic (import issues, slow training), use scikit-learn on a toPandas() conversion. Less "Databricks-native" but guaranteed to work. Log to MLflow via `mlflow.sklearn.log_model()` instead of `mlflow.spark.log_model()`.

**Person B: Voice Integration + Dashboard Start**

Goal: Voice agent reads real data from Databricks. Dashboard shows farmer profiles.

1. Build the Databricks connector module for the local voice agent — functions to read profile, score, strategy.
2. Integrate the connector into the Pipecat bot — pre-load farmer context into the Gemini system prompt before the call starts.
3. Test a full voice conversation: speak Hindi, get Hindi response that references the farmer's actual data.
4. Add conversation logging — each turn writes to `conversation_log` Delta table.
5. Start building the Streamlit dashboard — Tab 1 (Farmer Profile) reading from Silver table, Tab 2 (Credit Assessment) reading from scored_profiles.

**Checkpoint at 4:30**: Voice agent talks about the right farmer's data. Dashboard shows at least 2 tabs with real data.

---

### 4:30 PM – 6:00 PM | Integration Sprint (Both Together)

Goal: End-to-end pipeline works for 1 farmer. Rough but complete.

1. Test the two-phase flow: "Run Analysis" button first triggers ML scoring notebook → waits for `scored_profiles` to be populated → THEN triggers agent pipeline.
2. Verify Agent 3 (GrameenScorer) reads pre-computed scores from `scored_profiles` Delta table — NOT from any model.
3. Connect the agent pipeline output to the dashboard — Agent 5's loan strategy should appear in Tab 3.
4. Test the full flow: select farmer → ML scores → agents run → score + strategy appear → approve → voice call works.
5. Identify the top 3 blockers for overnight and assign them.

**Checkpoint at 6:00**: The two-phase flow (ML then agents) works for 1 farmer. Both members have seen the entire flow.

---

## Overnight (6:00 PM – 9:00 AM)

### Priority order for overnight work:

1. **P0: Dashboard completion** — All 5 tabs functional, connected to real Delta data. Deploy as Databricks App. If deployment fails, have ngrok ready as backup.

2. **P0: FAISS RAG index** — Chunk scheme documents, embed with MiniLM, build FAISS index, save to DBFS. Wire into Agent 2's tool. This replaces the stub from earlier.

3. **P0: 3 demo farmer profiles** — Create 3 distinct farmers: (a) strong candidate (small farmer, good savings, PM-KISAN enrolled → score ~78), (b) moderate candidate (medium farmer, high seasonality, one previous default → score ~55), (c) weak candidate (landless, no bank history, high DTI → score ~32). Each should produce different scores, strategies, gap analyses, AND agricultural advisory plans. These are the demo scenarios.

4. **P0: Crop calendar reference table** — Build the `silver_crop_calendar` Delta table with 50-80 rows covering 10-15 major crops across 3-4 agro-climatic zones. Data from ICAR Package of Practices guides (publicly available). Include sowing windows, seed rates, fertilizer doses, water requirements, expected yields, and MSP prices. Also build the district-to-zone lookup table. This takes 1-2 hours but is essential for Agent 6 (AgriAdvisor) to give specific, credible farming advice.

5. **P0: Agent 6 (AgriAdvisor)** — Build the AgriAdvisor agent with its tools (district_agri_lookup, msp_price_lookup, crop_calendar_lookup). Test with the 3 demo profiles. Each farmer should get a different sowing plan, different input cost estimates, and a different repayment cash flow map. This agent's output is what makes the voice call feel genuinely useful.

6. **P1: Voice agent polishing** — Expand system prompt with the AgriAdvisor output. Test the full 3-phase conversation flow. Make sure the agent covers sowing advice, input costs, market timing, and the repayment cash flow plan. Ensure logging works.

7. **P1: Delta Lake demonstrations** — Implement MERGE INTO for profile updates, time-travel query for showing profile evolution, DESCRIBE HISTORY on conversation_log. These are "show Databricks depth" moments.

8. **P2: Edge case handling** — What happens with a farmer who has no bank history? No land? Existing defaults? The system should handle gracefully, not crash.

9. **P2: GitHub repo** — Push all code. Write README. Create architecture diagram.

**REST**: Set alarm for 8 AM. Day 2 is mentally demanding — pitch prep and live demo debugging.

---

## Day 2: 9:00 AM – 3:00 PM

### 9:00 – 11:00 AM | Testing & Hardening

1. Full end-to-end test with all 3 demo farmer profiles.
2. Fix any overnight breakages (APIs that stopped working, tables that got corrupted).
3. Test on a browser you haven't used (judges may use a different browser).
4. Verify the Databricks App URL is accessible without authentication issues.
5. Run the voice agent — do a complete 2-minute call with one farmer profile.
6. Take screenshots: MLflow experiment comparison, Delta Lake history, dashboard views.

### 11:00 AM – 1:00 PM | Demo Preparation

1. **Record the 2-minute demo video** (mandatory submission requirement). Screen record with narration. Show: dashboard → ML scoring → agent pipeline → **HERO: voice agent advising farmer in Hindi on both loan terms AND crop strategies** → dashboard showing live transcript. Narrate what's happening and why.

2. **Prepare the 5-minute pitch** (if selected for presentations):
   - 30 seconds: Problem ("ULI processes loans in 10 minutes. But 16% become NPAs because farmers get zero post-disbursement support. The problem isn't getting the loan — it's repaying it.")
   - 1.5 minutes: Architecture + approach (show the diagram, explain Databricks components, ML scoring pipeline, name the Indian models)
   - 2 minutes: **LIVE DEMO — THE VOICE CALL** (this is the hero moment. Show the AI advisor calling a farmer in Hindi, explaining loan terms, then proactively advising: "Chana bhi lagaaiye, MSP zyada hai" and "Agle hafte baarish hai, spray mat kariye." The judges should HEAR the agent giving farming advice tied to loan repayment.)
   - 1 minute: Impact + Future ("This reduces NPAs by coaching farmers to succeed. Future: periodic follow-up calls at sowing, mid-season, harvest, and repayment — the AI becomes a trusted agricultural advisor. Trained on 307K real loan records + ICRISAT district-level crop data.")

3. **Rehearse** at least twice. Time it. Cut anything over 5 minutes ruthlessly.

4. **Prepare backup plans**: Pre-recorded video if live demo fails. Pre-loaded data if pipeline is slow. Talking points if judges ask tough questions:
   - "How is this different from ULI?" → "ULI automates loan PROCESSING. We help with loan REPAYMENT. ULI ends at disbursement — we start there. The voice agent doesn't just explain terms, it coaches the farmer on crop strategy, weather-based timing, and income diversification to ensure they CAN repay."
   - "Why synthetic data?" → "Parameterized by NABARD/ICRISAT real statistics."
   - "Why not CIBIL?" → "Government mandated Grameen Credit Score as an alternative for the 86% of farmers who are small/marginal."
   - "Is the voice agent just a gimmick?" → "No. 70% of Indian farmers are not comfortable with apps or forms. A Hindi voice call is the NATURAL interface for rural advisory. And the advisory content is data-driven — weather forecasts, MSP prices, district crop yields, all from real sources."

### 1:00 – 3:00 PM | Submission

1. Verify GitHub repo is PUBLIC and will remain so for 30 days.
2. Submit: GitHub link, 500-character writeup, demo video link, Databricks App URL.
3. Verify all submitted links work from an incognito browser.
4. Add final README touches: Databricks technologies listed, Indian models listed, architecture diagram.
5. Clean up notebook comments — judges will read the code.

---

## Submission Deliverables Checklist

| Item | Status | Notes |
|------|--------|-------|
| Public GitHub repo | ☐ | Must include README, architecture diagram, runnable code |
| Architecture diagram in README | ☐ | Show how Databricks components connect |
| "How to run" with exact commands | ☐ | Judges will attempt to reproduce |
| Demo steps (what to click/prompt) | ☐ | Step-by-step walkthrough |
| 500-character project writeup | ☐ | What + why, concise |
| 2-minute demo video | ☐ | Screen recording with narration |
| Deployed prototype link | ☐ | Databricks App URL |
| Databricks technologies list | ☐ | Name all 8 components used |
| Open-source models list | ☐ | Sarvam, Gemini, IndicTrans2 |
| MLflow experiment logs (bonus) | ☐ | Screenshot or link |
| Quantitative accuracy metrics (bonus) | ☐ | AUC-ROC, F1, etc. |

---

## Risk Decision Matrix

| Scenario | Detection | Response | Recovery Time |
|----------|-----------|----------|---------------|
| Databricks App won't deploy | "Compute error" on creation | Use ngrok to tunnel local Streamlit | 10 minutes |
| Gemini rate limited (15 RPM) | 429 errors during agent pipeline | Pre-compute agent outputs for demo profiles, serve from cache | 30 minutes |
| Sarvam API down during demo | No STT/TTS response | Play pre-recorded demo video, show code + architecture | 5 minutes |
| MLflow not available on Free Edition | Import error or feature flag | Use mlflow locally, screenshot results | 20 minutes |
| Home Credit dataset too large for compute quota | Out of memory or slow processing | Subsample to 50K rows — still more than enough for training | 15 minutes |
| Voice latency > 3 seconds | Unnatural conversation feel | Shorten LLM responses to 1 sentence, pre-cache common Q&As | 30 minutes |
| FAISS index build fails | Memory or dependency issues | Hardcode top 5 schemes with rules — no RAG needed for 5 schemes | 20 minutes |
| Judges can't reproduce from GitHub | Build fails on fresh workspace | Create a single "00_run_everything.py" notebook that does setup + demo | Test this explicitly |