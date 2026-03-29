# DATA_PIPELINE.md — Datasets, Transformation Logic & Delta Lake Strategy

## Data Philosophy

The credibility of the ML model depends entirely on data quality. The strategy is **hybrid**: train on real public datasets from Indian government sources and Kaggle, augmented with targeted synthetic data only where real data has gaps. Every synthetic parameter (income distributions, default rates, seasonal patterns) is calibrated against published NABARD, RBI, and ICRISAT statistics. When judges ask "is this trained on real data?" the answer is "yes — 7 real datasets, with synthetic augmentation parameterized by government statistics."

---

## Current Implementation Status

### Delta Tables in Active Use

The following tables are actively referenced in the current codebase (`krishirin_agents/shared/config.py` and `backend/databricks_client.py`):

| Table | Layer | Used By | Purpose |
|-------|-------|---------|---------|
| `krishirin.loan_advisory.silver_farmer_profile` | Silver | data_loader agent, backend briefing API | Farmer demographics, land, crops, loans, bank summary |
| `krishirin.loan_advisory.scored_profiles` | Scored | data_loader agent, backend briefing API | ML outputs: grameen_score, risk_category, repayment_prob, risk_cluster, predicted_capacity, factors |
| `krishirin.loan_advisory.silver_district_features` | Silver | data_loader agent | District-level ag metrics: avg yield, irrigation %, rainfall, crop failure rate, soil type |
| `krishirin.loan_advisory.silver_crop_calendar` | Silver | data_loader agent | Sowing/harvest windows, seed rates, fertilizer doses, water requirements per crop per zone |
| `krishirin.loan_advisory.bronze_msp_prices` | Bronze | data_loader agent | MSP per quintal for 22 crops |
| `krishirin.loan_advisory.precall_analysis` | Output | precall_synthesis agent (writes) | Complete precall pipeline output |
| `krishirin.loan_advisory.loan_strategies` | Output | backend results API | Recommended loan terms per farmer |
| `krishirin.loan_advisory.agri_advisory_plans` | Output | backend results API | Agricultural advisory (sowing plan, costs, market timing, cashflow) |
| `krishirin.loan_advisory.conversation_log` | Audit | backend (writes during voice calls) | Voice call transcripts: farmer_id, turn_number, speaker, text, call_type |

### Two Database Client Implementations

1. **`backend/databricks_client.py`**: Used by the FastAPI server for API endpoints. Singleton pattern with `is_configured` check. Methods: `query()`, `execute()`, `get_farmer_profile()`, `get_scored_profile()`, `get_loan_strategy()`, `get_agri_advisory()`, `log_conversation_turn()`.

2. **`krishirin_agents/shared/delta_client.py`**: Used by ADK agents. Functions: `get_connection()`, `query_one()`, `query_all()`, `execute_write()`.

Both connect via `databricks-sql-connector` using the same `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `DATABRICKS_HTTP_PATH` environment variables.

### Sample Data Fallback

When Databricks is not configured (`USE_SAMPLE_DATA=True` in `krishirin_agents/shared/config.py`), the system uses hardcoded sample data from `krishirin_agents/shared/sample_data.py`:

**Sample Farmer: Ramesh Patil**
- Age: 42, District: Nashik (Maharashtra)
- Land: 3 acres owned, mixed irrigation
- Crops: Soybean, Onion, Wheat
- Existing loans: ₹50K SBI crop loan, active, ₹2.5K/month EMI
- Govt schemes: PM-KISAN enrolled
- Bank: 12 months history, ₹18K avg monthly income, ₹4.5K/month savings (25% rate)
- Aadhaar: ****7834

**Sample ML Scores:**
- Grameen Score: 68.5/100 (Category B, Moderate Risk)
- Repayment probability: 0.78
- Risk cluster: 1
- Predicted capacity: ₹2,00,000
- Top positive: Regular savings, 12-month consistency, land ownership, PM-KISAN, mixed irrigation
- Top negative: 35% income seasonality, existing crop loan, single-district dependency

**Sample District Data (Nashik):**
- Avg yield: 12.5 q/ha, Irrigation: 45%, Rainfall: 600mm, Failure rate: 12%
- Dominant crops: Onion, grape, soybean, wheat, tomato
- Soil: Black cotton (Regur)

**Sample Weather (Mocked):**
- Current: 32.5°C, 45% humidity, partly cloudy
- 7-day forecast included

This allows the entire system (backend, agents, voice pipeline) to run fully functional without any Databricks connection.

### Weather Data Integration

`krishirin_agents/shared/weather_client.py` fetches live weather from OpenWeatherMap API:
- Maps 20+ Indian districts to (lat, lon) coordinates
- Returns: current conditions (temp, humidity, description, wind, rain) + 7-day daily forecast
- Used by `data_loader_agent` via `fetch_weather_data` tool
- Free tier: 1,000 calls/day

### FAISS Vector Index

`krishirin_agents/shared/faiss_client.py` provides RAG search over scheme documents:
- Embedding model: sentence-transformers `all-MiniLM-L6-v2` (22MB, CPU-friendly)
- Index and chunks loaded from paths in config (`FAISS_INDEX_PATH`, `FAISS_CHUNKS_PATH`)
- `search(query, top_k=5)` returns: scheme_name, text chunk, source file, similarity score
- Used by `scheme_rag_agent` in precall pipeline (runs 4 search queries)

---

## Dataset Inventory (Design Reference)

### Dataset 1: Home Credit Default Risk (Kaggle)

**What it is**: 307,511 loan applicants with binary default labels (TARGET: 0 = repaid, 1 = defaulted). Includes 7 linked tables covering credit bureau history, previous loan applications, actual repayment records, and credit card balances.

**Why it's the primary training dataset**: Home Credit specifically designed this dataset for predicting repayment ability of the unbanked population using alternative data — telco data, transactional patterns, social network signals. This is philosophically identical to the Grameen Credit Score mandate. The alternative data features (EXT_SOURCE scores, bureau data, payment behavior) map directly to our Grameen scoring approach.

**What to use from it**: The `application_train.csv` provides the core features and labels. The `bureau.csv` gives credit history depth. The `installments_payments.csv` provides actual repayment behavior patterns. The `previous_application.csv` shows how applicants behaved on prior loans.

**Transformation logic for Silver**: Select the most relevant columns — income, credit amount, annuity, external scores, age (derived from DAYS_BIRTH), employment duration (from DAYS_EMPLOYED), property ownership, family size. Compute derived ratios: DTI (annuity/income), credit-to-income, payment-to-credit. Handle nulls — EXT_SOURCE columns have significant missing values; impute with median. The TARGET column (default flag) becomes the training label, inverted to `repaid_on_time` (1 = repaid, 0 = defaulted).

**Critical detail**: The Home Credit data is not Indian-specific. It comes from a Czech Republic lending institution. This is acceptable because the underlying behavioral patterns (income stability → repayment ability) are universal, and we're re-engineering the features to match agricultural contexts. Judges may ask about this — explain that the behavioral ML patterns are transferable, and the agricultural features come from ICRISAT.

### Dataset 2: ICRISAT District-Level Database

**What it is**: The most comprehensive district-level agricultural dataset for India. Maintained since 1966 by the International Crops Research Institute for the Semi-Arid Tropics, in partnership with Cornell University. Contains 74 datasets, 1,030 variables, over 11 million data points covering 571 districts across 20 states.

**Why it's essential**: It provides the agricultural context that makes this project uniquely Indian. When a farmer says "I'm in Nashik district growing grapes and onions," the system needs to know Nashik's average crop yields, irrigation rates, rainfall patterns, and historical crop failure rates. This data turns a generic credit scorer into an agriculture-aware credit scorer.

**What to use from it**: Four data files — crop area/production/yield (20 major crops per district per year), rainfall (monthly district-level), irrigation (source-wise: canals, tanks, wells, tubewells), and land holdings (distribution by size class: marginal, small, medium, large). Each file spans decades, but use the most recent 10 years for feature computation.

**Transformation logic for Silver**: Aggregate to current district-level summaries — average yield per major crop, percent irrigated area, average annual rainfall, yield volatility (standard deviation over 10 years), crop failure rate (years where yield dropped below 50% of expected). Create a composite `district_crop_risk_index` as (crop_failure_years / total_years). Join with MSP prices to create `land_productivity_estimate` per crop per district.

**Key challenge**: ICRISAT data comes in Excel format with sometimes inconsistent column names and district name spellings across years. District boundaries have changed over time (new districts created from older ones). The "apportioned" datasets handle this by mapping new districts back to historical parent districts. Use the un-apportioned version for simplicity.

### Dataset 3: District-wise Crop Production Statistics (data.gov.in)

**What it is**: Official Government of India data from the Directorate of Economics & Statistics covering district-wise, crop-wise, season-wise area (hectares) and production (tonnes) from 1997 to present.

**Why it complements ICRISAT**: While ICRISAT covers 20 major crops, this dataset covers all crops including minor ones. It's also more frequently updated. Combined with MSP prices, it enables precise income estimation for any farmer based on their specific crops, acreage, and district.

**Transformation logic**: Group by district and crop. Compute average yield (production/area) per crop per district. Join with MSP prices to get estimated revenue per hectare per crop. This becomes the `land_productivity_estimate` feature — the most direct measure of a farmer's earning potential.

### Dataset 4: MSP (Minimum Support Prices)

**What it is**: The Government of India fixes MSP for 22 mandated agricultural crops each year. This is the guaranteed minimum price at which government agencies procure farm produce.

**Why it's critical for income estimation**: MSP × district average yield × farmer's acreage = estimated annual crop income. This is how real bank loan officers estimate farmer income. Using it makes the system credible.

**Transformation logic**: Create a simple lookup table: crop name, MSP per quintal, marketing season, year. This is a small reference table (22 rows) used in joins during feature engineering.

### Dataset 5: Hackathon-Provided Synthetic UPI Transactions

**What it is**: The hackathon organizers provide "Synthetic UPI Transactions" as a dataset under the Digital-Artha track. Details will be shared on Day 1.

**Why to use it**: It's transaction-level data that can be used for financial feature engineering. Using the hackathon-provided dataset shows the judges you engaged with their resources.

**Transformation logic**: Depends on the schema (revealed Day 1). Expected to have timestamp, amount, type (credit/debit), counterparty fields. Use PySpark to aggregate into monthly summaries per user — same pipeline as the bank statement feature engineering.

### Datasets 6-8: Enrichment Sources

**Agriculture Loan Disbursement (data.gov.in)**: State-wise loan volumes help calibrate realistic loan amount distributions. If Maharashtra disbursed ₹1.2 lakh crore to X million accounts, average loan ≈ ₹Y. Use to parameterize synthetic data generation.

**Indian Agriculture Comprehensive (Kaggle)**: Cost of cultivation data per crop helps estimate farming expenses, improving the debt-to-income ratio accuracy.

**Government Scheme Documents (for RAG)**: Full text of KCC guidelines, PMFBY rules, PM-KISAN eligibility, MUDRA categories, and the RBI's Grameen Credit Score framework document. Converted to plain text, chunked for RAG embedding. These are NOT tabular data — they're the knowledge base for the Eligibility Agent.

### Dataset 9: Live Weather Data (OpenWeatherMap API)

**What it is**: Real-time weather conditions and 7-day forecast for any location via the OpenWeatherMap API. Free tier allows 1,000 API calls per day — more than enough for the hackathon.

**Why it's critical for the voice agent**: The FarmerAdvisor voice agent gives agricultural advice tied to weather conditions. If rain is forecast next week, the agent tells the farmer to delay spraying pesticides. If a dry spell is coming, it advises irrigation planning. This makes the advisory feel live and relevant — not static textbook advice.

**How it's used**: Called by the `data_loader_agent` via `fetch_weather_data` tool during precall pipeline Stage 1. The response (temperature, humidity, weather description, 7-day forecast) is stored in `farmer_context` state and passed to all downstream agents. Also pre-loaded into the voice agent's system prompt before calls. The implementation is in `krishirin_agents/shared/weather_client.py` with 20+ Indian districts mapped to (lat, lon) coordinates.

**Not stored in Delta**: This is a transient API call, not a dataset for ML training. It enriches the voice agent's context for one conversation. The weather information referenced during the call is captured in the `conversation_log` as part of the transcript.

### Dataset 10: Crop Calendar & Agricultural Practices (Used by Precall data_loader + Oncall crop_planner)

**What it is**: A structured reference table of crop-wise agricultural practices for India's major agro-climatic zones. Compiled from ICAR (Indian Council of Agricultural Research) Crop Production Technology guides, KVK (Krishi Vigyan Kendra) recommendations, and state agricultural university extension bulletins.

**Current implementation**: Loaded by `data_loader_agent` via `load_crop_calendar` tool from `krishirin.loan_advisory.silver_crop_calendar` Delta table. Also available in sample data (`krishirin_agents/shared/sample_data.py`) for offline testing.

**What it contains per crop per zone**: Optimal sowing window (date range), expected growing days, harvest window, seed rate (kg/hectare), recommended fertilizer dose (N:P:K kg/hectare), water requirement (mm total and critical growth stages), common pests and diseases with treatment, expected yield (quintals/hectare), and cost of cultivation estimate (₹/hectare).

**Why it's essential**: Agent 6 (AgriAdvisor) needs this to build specific sowing plans. Without it, the agent gives generic advice. With it, the agent can say: "Nashik mein Kharif soybean ki bua-ee June 15-30 ke beech kariye, 75 kg beej per hectare, DAP 100 kg aur Urea 25 kg daaliye, 450mm paani chahiye" — concrete, actionable, district-relevant advice.

**How to build it for the hackathon**: Create a `silver_crop_calendar` Delta table with approximately 50-80 rows covering the 10-15 most important crops (rice, wheat, soybean, cotton, chana/gram, moong, tur, jowar, bajra, maize, groundnut, onion, sugarcane, mustard, sunflower) across 3-4 major agro-climatic zones (Western Maharashtra plateau, Indo-Gangetic plains, Central/Vidarbha, and South peninsular as examples). Data compiled from publicly available ICAR Package of Practices documents and state agriculture department websites. This is a one-time reference table, not a large dataset — 80 rows with 15 columns.

**Key columns**: crop_name, agro_climatic_zone, season (Kharif/Rabi/Zaid), sowing_window_start, sowing_window_end, harvest_window_start, harvest_window_end, growing_days, seed_rate_kg_per_ha, fertilizer_n_kg, fertilizer_p_kg, fertilizer_k_kg, water_requirement_mm, expected_yield_q_per_ha, cultivation_cost_per_ha, common_pests (text list), msp_per_quintal.

### Dataset 11: Agro-Climatic Zone Mapping

**What it is**: A lookup table mapping each Indian district to its agro-climatic zone. India has 15 agro-climatic zones defined by the Planning Commission based on soil type, rainfall, and temperature patterns.

**Why it's needed**: When the AgriAdvisor agent looks up crop recommendations, it needs to know which zone the farmer's district falls in. A Nashik farmer gets different advice from a Punjab farmer even for the same crop.

**How to build it**: A simple lookup table with ~700 rows (one per district). The mapping is available in ICAR publications and on the National Informatics Centre website. For the hackathon, cover the 100-150 districts most likely to appear in demo scenarios. The rest default to their state's dominant zone.

---

## Synthetic Data Augmentation Strategy

**Where real data has gaps**: We have real loan default labels (Home Credit) and real agricultural context (ICRISAT), but we don't have real Indian farmer bank transaction data at the individual level (that's proprietary bank data). We also don't have labeled Grameen Credit Score outcomes (the framework is brand new — no historical data exists).

**How to fill the gaps responsibly**:

Generate 5,000 synthetic farmer profiles. Each profile includes 12 months of transaction data (credits, debits, balances). The generation is parameterized by real statistics:

**Income distributions**: Match NABARD data (average loan disbursed per account ≈ ₹1.02 lakh). Small/marginal farmer income ≈ ₹8,000-12,000/month. Medium farmer ≈ ₹15,000-25,000. Large farmer ≈ ₹30,000-50,000.

**Farmer archetype distribution**: 55% small/marginal (matching India's 86.1% small/marginal farmer ratio, adjusted for those who apply for loans), 25% medium, 10% large, 10% landless-allied.

**Seasonality patterns**: Kharif harvest (Oct-Dec) shows 1.8-3× income spike. Rabi harvest (Mar-May) shows 1.5-2.5× spike. Lean season (Jun-Aug) shows 0.3-0.7× dip. This matches India's actual agricultural cycle.

**Government transfers**: 65% of farmers receive PM-KISAN (₹2,000 every 4 months), matching national coverage data.

**Default rates**: 16-18% for small/marginal (matching RBI NPA data for agricultural loans from TransUnion CIBIL), 10% for medium, 5% for large, 22% for landless.

**Default correlates**: Higher DTI ratio → higher default probability. High income seasonality → higher default. Participation in government schemes → lower default. Strong savings consistency → lower default. These correlations are based on published agricultural credit research.

**Label generation**: The `repaid_on_time` label is not random — it's generated as a probabilistic function of the farmer's features, with base default probabilities per archetype modified by financial behavior signals. This ensures the ML model learns real-world-calibrated patterns.

---

## Bronze → Silver Transformation Rules

**Rule 1: Type enforcement.** Every column must have an explicit type. No "inferred" types. Farmer_id is always STRING. Amounts are always FLOAT. Counts are always INT. Dates are always TIMESTAMP.

**Rule 2: Null handling.** Never silently drop nulls. For numeric columns, impute with median (not mean — more robust to outliers). For categorical columns, create an explicit "unknown" category. Log null counts per column to MLflow as data quality metrics.

**Rule 3: Masking PII.** Aadhaar numbers must be masked to last 4 digits. Bank account numbers masked. PAN numbers stored only if needed for cross-verification. This is both good practice and demonstrates awareness of data privacy regulations.

**Rule 4: Monthly aggregation.** Raw transaction data (daily or per-transaction rows) must be aggregated to monthly level before feature engineering. Group by farmer_id and month. Sum credits, sum debits, compute end-of-month balance, count unique counterparties. This reduces data volume and creates the temporal resolution needed for seasonality analysis.

**Rule 5: District joining.** Every farmer profile must be enriched with their district's agricultural data. The join key is (district_name, state). Handle the fact that district names may have different spellings or transliterations (e.g., "Nashik" vs "Nasik"). Use fuzzy matching or maintain a district name normalization lookup.

---

## Delta Lake Operations That Earn Points

The judges evaluate whether Delta Lake is "actually doing work, or just present." These operations demonstrate meaningful usage:

**MERGE INTO**: When a farmer submits additional documents, use MERGE to update their Silver profile without duplicating rows. This shows incremental data handling, not just bulk overwrites.

**Time Travel**: Query a farmer's profile as it existed at a previous point in time. This demonstrates the audit trail capability. Show this in the demo: "Here's how this farmer's creditworthiness evolved over their last 3 interactions."

**Schema Evolution**: If the agent pipeline produces a new output field that didn't exist before (like a new risk flag), ALTER TABLE to add the column. This shows the schema can grow without breaking existing queries.

**DESCRIBE HISTORY**: Show the version history of a Delta table during the demo. This proves the data has lineage and is auditable — critical for financial applications.

**Partition and optimization**: Partition the Gold table by state for efficient querying. Run OPTIMIZE on frequently-read tables. These are small touches that show platform fluency.