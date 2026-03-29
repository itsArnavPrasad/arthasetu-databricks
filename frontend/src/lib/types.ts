// ===== Farmer & Application Types =====

export interface FarmerProfile {
  farmer_id: string;
  name: string;
  aadhaar_last4: string;
  district: string;
  state: string;
  land_holding_acres: number;
  land_type: "owned" | "leased" | "shared" | string;
  irrigation_type?: string;
  crops: string[];
  existing_loans: ExistingLoan[];
  govt_schemes: string[];
  bank_summary: BankSummary;
  data_completeness?: Record<string, boolean>;
}

export interface ExistingLoan {
  type: string;
  amount?: number;
  outstanding?: number;
  emi?: number;
  status?: "active" | "closed" | "defaulted" | "overdue" | string;
  lender?: string;
}

export interface BankSummary {
  avg_monthly_income?: number;
  avg_monthly_expense?: number;
  avg_balance?: number;
  months_of_history?: number;
  account_holder?: string;
  bank_name?: string;
  total_credits?: number;
  total_debits?: number;
}

export interface DocumentInfo {
  id: string;
  type: "aadhaar" | "bank_statement" | "loan_slip" | "land_record" | "crop_receipt" | "other";
  filename: string;
  status: "uploading" | "uploaded" | "processing" | "verified" | "error";
  uploadedAt: string;
}

export interface ApplicationStatus {
  farmer_id: string;
  phase: ApplicationPhase;
  documents: DocumentInfo[];
  ml_status: "pending" | "running" | "completed" | "error";
  agent_status: AgentPipelineStatus | null;
}

export type ApplicationPhase =
  | "apply"
  | "analysis"
  | "call1"
  | "processing"
  | "call2"
  | "summary";

// ===== ML & Scoring Types =====

export interface GrameenScore {
  grameen_score: number;
  risk_category: "A" | "B" | "C" | "D";
  repayment_prob: number;
  risk_cluster: number;
  predicted_capacity: number;
  top_positive_factors: string[];
  top_negative_factors: string[];
}

export interface PreCallBriefing {
  farmer: FarmerProfile;
  score: GrameenScore | { grameen_score: null; risk_category: null; status: string };
  flags: RiskFlag[];
  auto_questions: string[];
  ocr_complete?: boolean;
  ml_complete?: boolean;
}

export interface RiskFlag {
  type: "warning" | "critical" | "info";
  category: string;
  description: string;
  detail: string;
}

// ===== Agent Pipeline Types =====

export type AgentName =
  | "EligibilityChecker"
  | "GrameenScorer"
  | "GapAnalyzer"
  | "StrategyArchitect"
  | "AgriAdvisor";

export type AgentStatus = "pending" | "running" | "completed" | "error";

export interface AgentPipelineStatus {
  agents: {
    name: AgentName;
    status: AgentStatus;
    started_at?: string;
    completed_at?: string;
  }[];
  overall_progress: number; // 0-100
}

// ===== Results Types =====

export interface LoanStrategy {
  product: string;
  amount: number;
  tenure_years: number;
  interest_rate_nominal: number;
  interest_rate_effective: number;
  emi_monthly: number;
  total_repayment: number;
  collateral_required: boolean;
  collateral_details: string;
  repayment_schedule: RepaymentEntry[];
  rationale: string;
  alternative?: {
    product: string;
    amount: number;
    reason: string;
  };
}

export interface RepaymentEntry {
  month: string;
  amount: number;
  source: string;
  type: "kharif" | "rabi" | "regular" | "buffer";
}

export interface SchemeEligibility {
  scheme_name: string;
  eligible: boolean;
  match_percent: number;
  benefit_amount: string;
  missing_requirements: string[];
  details: string;
}

export interface AgriAdvisory {
  land_assessment: string;
  sowing_plan: SowingEntry[];
  input_cost_guidance: string;
  weather_guidance: string;
  market_timing: string;
  income_diversification: string;
  repayment_cashflow_map: CashflowEntry[];
}

export interface SowingEntry {
  crop: string;
  area_acres: number;
  season: "kharif" | "rabi" | "zaid";
  sowing_window: string;
  expected_yield_qtl: number;
  expected_revenue: number;
}

export interface CashflowEntry {
  month: string;
  income_sources: { source: string; amount: number }[];
  total_income: number;
  emi_due: number;
  surplus: number;
}

export interface GapAnalysis {
  critical_gaps: string[];
  warnings: string[];
  improvement_suggestions: string[];
  application_ready: boolean;
  readiness_score: number;
}

export interface AllResults {
  score: GrameenScore;
  loan_strategy: LoanStrategy;
  schemes: SchemeEligibility[];
  agri_advisory: AgriAdvisory;
  gap_analysis: GapAnalysis;
}
