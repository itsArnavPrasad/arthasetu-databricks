# ML_PIPELINE.md — Feature Engineering Logic, Model Design & Scoring Strategy

## Why ML Instead of LLM-Based Analysis

An LLM analyzing bank statements to produce a credit score would be: slow (10-30 seconds per farmer), non-deterministic (same farmer → different score each time), expensive (API costs per inference), and unexplainable ("the LLM said 72" is not acceptable for financial decisions). A proper ML pipeline is: fast (~50ms per farmer), deterministic, free at inference (model runs on Databricks compute), and explainable (feature importances show exactly why a farmer scored X).

The LLM's role is strictly limited to: (1) generating a human-readable explanation of the ML score, and (2) communicating the results in Hindi during the voice call. The analytical intelligence is pure ML. This is how production financial systems work — and judges will recognize the maturity of this design.

---

## The 42 Features: Design Rationale

Every feature is grounded in what real Indian agricultural lenders actually assess, mapped to the Grameen Credit Score framework's emphasis on alternative data. Features are organized into 5 families.

### FAMILY 1: Income & Cash Flow (Features 1-12)

These features answer: "How much does this farmer earn, and how stable is that income?" Agricultural income is inherently seasonal — a wheat farmer earns nothing for 8 months and makes their entire annual income during 2-3 harvest months. The features must capture both level and pattern.

**Feature 1 — Average monthly income**: The simplest signal. Mean of monthly credit amounts over 12 months. But for seasonal farmers, this is misleading — a farmer earning ₹0 for 6 months and ₹30,000 for 6 months has the same average as one earning ₹15,000 consistently. That's why we need Feature 4.

**Feature 2 — Median monthly income**: More robust to outlier months. A farmer with one exceptional harvest sale won't be overvalued. Use PySpark's `percentile_approx` function.

**Feature 3 — Income trend slope**: Is income growing or declining year-over-year? Computed as the difference between the average of the last 3 months and the first 3 months, divided by 9 (to normalize by time). A positive slope signals improving conditions.

**Feature 4 — Income seasonality index**: The coefficient of variation (standard deviation / mean) of monthly income. This is THE critical agricultural feature. A CV of 0.3 means relatively stable income (perhaps a dairy farmer with monthly milk sales). A CV of 2.0 means extreme seasonality (crop farmer with one annual harvest). High seasonality means high risk — the borrower must survive lean months without income.

**Features 5-6 — Kharif and Rabi season income**: Sum of credits during Kharif months (Jun-Nov) and Rabi months (Nov-Apr). Together, these reveal crop diversification. A farmer with income in both seasons has year-round earning and lower risk than one with income in only one season.

**Feature 7 — Off-season income ratio**: Income in non-harvest months divided by total income. High off-season income signals non-farm income sources (a job, remittances, dairy) that provide stability. This is a strong positive signal for loan repayment.

**Features 8-9 — Max and min monthly income**: The range tells you about vulnerability. If min is near zero, the farmer has months where they simply cannot repay a loan installment.

**Feature 10 — Income gap months**: Count of months with income below ₹500 (essentially zero). Three or more gap months in a year is a red flag — how will they repay an EMI during those months?

**Feature 11 — Government transfer income**: Detect PM-KISAN transfers (₹2,000 arriving periodically, roughly every 4 months). This serves dual purpose: it confirms the farmer is enrolled in government schemes (Grameen score boost), and it adds a guaranteed income floor.

**Feature 12 — Income source diversity**: Count of distinct counterparties (unique sources of income). A farmer receiving money from only one buyer is at high risk if that buyer relationship ends. Multiple sources signal a diversified market.

### FAMILY 2: Expenditure & Debt (Features 13-22)

These features answer: "How much does this farmer owe, and can they handle more debt?"

**Feature 14 — Debt-to-income ratio (DTI)**: The single most important credit metric in any lending context. Total monthly debt payments divided by monthly income. Above 0.4 is generally considered risky. For agricultural loans, this must account for seasonal income — the DTI should be computed against average monthly income, not just the current month.

**Feature 19 — EMI-like pattern count**: This is a killer feature for detecting existing undisclosed loans. Use PySpark to find recurring debit amounts: round each debit to the nearest ₹100, group by farmer and amount bucket, count occurrences. If the same amount appears 3+ times, it's likely an EMI. This catches loans the farmer didn't disclose — a common issue in rural lending where farmers borrow from multiple sources.

**Feature 22 — Expense-income correlation**: The Pearson correlation between monthly income and monthly expenses. A high positive correlation (spend more when earn more) actually signals financial discipline — the farmer adjusts spending to income. A near-zero correlation (spending stays high even in low-income months) signals living beyond means.

### FAMILY 3: Savings & Behavior (Features 23-30)

These features directly operationalize the Grameen Credit Score mandate. The GCS specifically requires assessing "savings habits" as an alternative data signal. Traditional credit scores ignore savings entirely.

**Feature 26 — Savings rate**: (Income - Expenditure) / Income, averaged monthly. Even a 5% savings rate signals financial discipline. Combined with Feature 23 (average balance), this tells you if the farmer builds a buffer.

**Feature 28 — Balance recovery speed**: After a balance dip below the median (e.g., a medical emergency or crop failure), how many months does it take to recover? Fast recovery signals resilience. Slow recovery signals financial fragility. Compute using PySpark window functions: identify dip events, find the next month where balance returns to median, count the gap.

**Feature 30 — Banking relationship length**: Total months of transaction history available. More months = more trust. A farmer with 24 months of steady banking history is more trustworthy than one with 3 months, even if the 3-month data looks good. Banks weight this heavily.

### FAMILY 4: Agricultural & Land Profile (Features 31-38)

These features come from the farmer's profile (land records, crop declarations) enriched with district-level ICRISAT data. They answer: "What is this farmer's productive capacity?"

**Feature 36 — Land productivity estimate**: Computed as: farmer's acreage × district average yield for their crop × MSP per quintal. This is how bank loan officers actually estimate farmer income when bank statements are unavailable. It provides a cross-check: if the bank statement shows ₹8,000/month but the land productivity estimate says the farmer should be earning ₹15,000/month, something doesn't add up (Feature 14 in gap analysis).

**Feature 37 — Irrigation access flag**: From ICRISAT district data or the farmer's profile. Irrigated land reduces crop failure risk dramatically. A farmer with irrigated land in a drought-prone district is far safer than a rainfed farmer in the same district.

**Feature 38 — District crop risk index**: Historical crop failure rate in the farmer's district, computed from ICRISAT data. Some districts (parts of Vidarbha, Bundelkhand) have chronic crop failure rates above 30%. This is an environmental risk the farmer cannot control — the model should factor it in.

### FAMILY 5: Scheme Participation & History (Features 39-42)

These features map directly to the Grameen Credit Score requirement of assessing "government program participation" and "micro-loan history."

**Feature 41 — Repayment history score**: Percentage of prior loans repaid on time. Research consistently shows this is the strongest predictor of future repayment. If the farmer has never borrowed institutionally before (thin file), this defaults to a neutral value (0.5), and the KMeans clustering (Model 2) handles risk assessment using behavioral data instead.

---

## Three-Model Ensemble Design

### Why Three Models Instead of One

A single GBTClassifier would get you to ~85% AUC-ROC and that's fine. But three models serve different purposes and handle different farmer segments better:

**Model 1 (GBT) handles thick-file farmers**: Those with credit history and labeled training data. It excels at predicting repayment for farmers similar to the training set.

**Model 2 (KMeans) handles thin-file farmers**: Those with no credit history at all. Since KMeans is unsupervised, it doesn't need labels. It clusters farmers into behavioral risk groups based purely on their financial patterns. A thin-file farmer with great savings behavior and diversified income lands in the low-risk cluster, even with zero credit history.

**Model 3 (RF Regressor) answers a different question**: "How much can this farmer repay?" rather than "Will they repay?" This determines the loan amount ceiling, not just approval/rejection.

The ensemble combines signals from all three: repayment probability × behavioral risk level × capacity headroom = holistic assessment.

### Model 1: GBTClassifier (Repayment Prediction)

**Algorithm**: Spark MLlib GBTClassifier (Gradient Boosted Trees). Chosen because gradient boosting consistently outperforms other algorithms for tabular credit scoring data in both academic literature and Kaggle competitions.

**Input**: All 42 features assembled via VectorAssembler and scaled via StandardScaler.

**Target**: `repaid_on_time` (binary: 1 = repaid, 0 = defaulted). Sourced from Home Credit labels (inverted TARGET) and synthetic data labels.

**Key hyperparameters to tune via CrossValidator**: maxDepth (try 4, 6, 8 — deeper trees risk overfitting), maxIter (try 50, 100, 200 — more iterations = better performance but slower), stepSize/learningRate (try 0.05, 0.1, 0.2 — lower = more robust but slower convergence), subsamplingRate (0.8 — randomly sample 80% of data per tree to prevent overfitting), featureSubsetStrategy ("sqrt" — randomly select √n features per split for diversity).

**Evaluation metrics**: AUC-ROC (primary — measures discriminative power across all thresholds), F1 score (secondary — balances precision and recall), Precision (important because approving a bad loan is costly), Recall (important because rejecting a good farmer perpetuates exclusion).

**Output**: The probability column from the GBT prediction (0.0 to 1.0) — NOT the binary prediction. The probability is the `repayment_score` component of the Grameen Score.

### Model 2: KMeans Clustering (Risk Profiling)

**Algorithm**: Spark MLlib KMeans with k=4 clusters, representing 4 risk tiers.

**Input**: Only financial behavior features (Families 1-3, features 1-30). Agricultural and scheme features are excluded because KMeans should cluster purely on behavioral patterns, not demographic proxies.

**Why k=4**: Mapping to standard banking risk categories: Low Risk, Moderate Risk, Elevated Risk, High Risk. Try k=3 through k=6 and pick the one with the best silhouette score.

**Post-processing**: After clustering, examine the cluster centers to determine which cluster corresponds to which risk level. The cluster with the highest average savings rate and lowest DTI is "Low Risk." The cluster with the highest income gap months and lowest balance is "High Risk." Assign labels accordingly. This mapping is done once and logged to MLflow.

**Why this is brilliant for the Grameen Score narrative**: The whole point of the Grameen Credit Score is that formal credit history shouldn't be required. KMeans proves this — it identifies creditworthy farmers purely from behavioral signals, even those with zero loan history. This is a strong talking point in the pitch.

### Model 3: RandomForestRegressor (Loan Capacity)

**Algorithm**: Spark MLlib RandomForestRegressor with 200 trees.

**Input**: All 42 features.

**Target**: `max_serviceable_loan` — a synthetic label computed as: `12 × net_monthly_surplus × desired_tenure_years × 0.75` (75% of theoretical maximum, as a safety margin). This represents how much loan the farmer could service based on their income minus expenses.

**Output**: A continuous value in ₹ representing the predicted safe loan ceiling.

**Usage in ensemble**: The `capacity_ratio` = predicted_capacity / requested_loan_amount. If the farmer asks for ₹2L but the model predicts they can only service ₹1.5L, the capacity_ratio is 0.75, which pulls the Grameen score down. If the model predicts ₹3L capacity but they only asked for ₹1L, capacity_ratio is capped at 1.5/1.5 = 1.0 (no bonus for asking for less than they can afford).

### Grameen Composite Score

The three model outputs combine as:

**Score = (0.40 × repayment_probability) + (0.25 × normalized_risk_score) + (0.35 × capacity_score)**

Scaled to 0-100. The weights reflect that repayment history is the strongest predictor (0.40), loan capacity matters almost as much (0.35), and behavioral risk adds the clustering signal (0.25).

**Risk categories**: A (≥75, Low Risk — strong candidate for full loan amount), B (55-74, Moderate Risk — approve with standard terms), C (35-54, Elevated Risk — reduced amount or shorter tenure recommended), D (<35, High Risk — consider rejecting or requiring co-borrower/additional collateral).

---

## MLflow Experiment Strategy

Run **6 experiments** to show methodical model selection. This earns bonus points (MLflow logs are explicitly mentioned in the submission requirements as an optional bonus).

**Experiment 1**: Logistic Regression baseline. Expected AUC ~0.68. This is the "naive benchmark" that proves the problem is non-trivial.

**Experiment 2**: RandomForestClassifier (100 trees, depth=6). Expected AUC ~0.78. Shows improvement over linear methods.

**Experiment 3**: GBTClassifier with default parameters. Expected AUC ~0.82. Shows GBT is superior for this problem.

**Experiment 4**: GBTClassifier with tuned parameters (depth=6, 100 iterations, subsample=0.8). Expected AUC ~0.86.

**Experiment 5**: GBT with CrossValidator (5-fold CV, full parameter grid). Expected AUC ~0.89. This is the final model.

**Experiment 6**: GBT with feature selection (top 25 features by importance). Expected AUC ~0.87. Shows that a simpler model is nearly as good — useful for interpretability.

For each experiment, log: all hyperparameters, AUC-ROC, F1, precision, recall, feature importances (as an artifact plot), training duration, and the model itself. Register the best model (Experiment 5) in the MLflow Model Registry as "grameen_repayment_gbt" with stage "Production."

Take a screenshot of the MLflow experiment comparison view (all 6 runs side by side) for the GitHub README. This single image tells the story of methodical model development better than any paragraph.

---

## Batch Scoring Output — What Gets Written to `scored_profiles`

The ML scoring notebook is a self-contained Databricks notebook that runs INDEPENDENTLY of the agent pipeline. When it completes, it writes one row per farmer to the `scored_profiles` Delta table with these columns:

- `farmer_id` — the unique farmer identifier
- `grameen_score` — the composite score (0-100), computed from the weighted ensemble
- `risk_category` — A/B/C/D derived from the score thresholds
- `repayment_prob` — raw probability from Model 1 (GBTClassifier), 0.0 to 1.0
- `risk_cluster` — cluster assignment from Model 2 (KMeans), 0 to 3
- `predicted_capacity` — predicted max loan amount from Model 3 (RF Regressor), in ₹
- `top_positive_factors` — the 3 features with highest positive contribution to the score (from feature importances)
- `top_negative_factors` — the 3 features with highest negative contribution
- `scoring_timestamp` — when the scoring ran
- `model_version` — MLflow model version used

This table is the ONLY interface between the ML pipeline and the agent pipeline. The agents never touch Spark MLlib, MLflow, or any model artifact. They just read this table.

---

## Explainability Layer

The human-readable explanation of the score can be generated in two places, depending on the workflow:

**Option A (recommended for hackathon)**: Agent 3 (GrameenScorer) reads the pre-computed score and factor breakdowns from `scored_profiles` and uses Gemini 2.0 Flash to generate the explanation. This keeps the ML notebook simple (just scoring) and gives the agent the role of communication. The agent reads stored numbers and translates them to plain language.

**Option B (alternative)**: The ML scoring notebook itself makes a single Gemini API call after scoring to generate the explanation, and stores it in a `score_explanation` column in `scored_profiles`. This pre-computes explanations in batch but adds an LLM dependency to the ML notebook.

For the hackathon, **Option A is cleaner** — it keeps ML notebooks purely about data and models, and keeps LLM calls in the agent layer. The agent reads the stored `top_positive_factors` and `top_negative_factors` from the Delta table and generates the explanation from those. No model is invoked.

**Why this design matters**: The ML model is the source of truth for the number. The LLM (via the agent) is the translator for the human. If the LLM hallucinates or gives bad advice, the score itself is still correct and auditable in the Delta table. This separation is a best practice in AI-assisted financial services.