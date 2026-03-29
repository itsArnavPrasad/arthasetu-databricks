"use client";

import { CreditCard, Calendar, Percent, ShieldCheck } from "lucide-react";

interface LoanStrategyCardProps {
  strategy: Record<string, unknown>;
}

export function LoanStrategyCard({ strategy }: LoanStrategyCardProps) {
  if (!strategy || typeof strategy !== "object") return null;

  // Handle array of strategies — take the first one
  const raw = Array.isArray(strategy) ? strategy[0] : strategy;
  if (!raw || typeof raw !== "object") return null;
  const s = raw as Record<string, unknown>;

  // Extract fields flexibly (agents may use different key names)
  const product = (s.product ?? s.recommended_scheme ?? s.scheme ?? "") as string;
  const amount = Number(s.amount ?? s.final_amount ?? s.loan_amount ?? 0);
  const rate = Number(s.interest_rate_effective ?? s.final_rate_effective ?? s.interest_rate ?? 0);
  const tenure = Number(s.tenure_years ?? s.tenure_months ? Math.round(Number(s.tenure_months) / 12) : 0);
  const emi = Number(s.emi_monthly ?? s.monthly_emi ?? s.emi ?? 0);
  const collateralRequired = Boolean(s.collateral_required);
  const collateralDetails = (s.collateral_details ?? s.collateral_plan ?? "N/A") as string;
  const rationale = (s.rationale ?? s.reasoning ?? "") as string;
  const schedule = Array.isArray(s.repayment_schedule) ? s.repayment_schedule : [];

  if (!product && !amount) {
    // No meaningful data — show raw JSON
    return (
      <div className="rounded-xl border border-krishirin-border bg-krishirin-surface p-5">
        <h3 className="font-semibold text-krishirin-text mb-3 flex items-center gap-2">
          <CreditCard className="w-5 h-5 text-krishirin-primary" />
          Loan Strategy
        </h3>
        <pre className="text-xs text-krishirin-text-muted bg-gray-50 rounded-lg p-3 overflow-auto max-h-60 whitespace-pre-wrap">
          {JSON.stringify(strategy, null, 2)}
        </pre>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-krishirin-border bg-krishirin-surface p-5">
      <h3 className="font-semibold text-krishirin-text mb-4 flex items-center gap-2">
        <CreditCard className="w-5 h-5 text-krishirin-primary" />
        Recommended Loan Strategy
      </h3>

      {/* Main terms */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        {product && (
          <div className="bg-krishirin-primary/5 rounded-lg p-3 text-center">
            <div className="text-xs text-krishirin-text-muted mb-1">Product</div>
            <div className="text-sm font-bold text-krishirin-primary">{product}</div>
          </div>
        )}
        {amount > 0 && (
          <div className="bg-krishirin-primary/5 rounded-lg p-3 text-center">
            <div className="text-xs text-krishirin-text-muted mb-1">Amount</div>
            <div className="text-sm font-bold text-krishirin-primary">
              ₹{amount >= 100000 ? `${(amount / 100000).toFixed(1)}L` : amount.toLocaleString("en-IN")}
            </div>
          </div>
        )}
        {rate > 0 && (
          <div className="bg-krishirin-primary/5 rounded-lg p-3 text-center">
            <div className="text-xs text-krishirin-text-muted mb-1 flex items-center justify-center gap-1">
              <Percent className="w-3 h-3" /> Interest
            </div>
            <div className="text-sm font-bold text-krishirin-primary">{rate}%</div>
          </div>
        )}
        {tenure > 0 && (
          <div className="bg-krishirin-primary/5 rounded-lg p-3 text-center">
            <div className="text-xs text-krishirin-text-muted mb-1 flex items-center justify-center gap-1">
              <Calendar className="w-3 h-3" /> Tenure
            </div>
            <div className="text-sm font-bold text-krishirin-primary">{tenure} years</div>
          </div>
        )}
      </div>

      {/* EMI and collateral */}
      {(emi > 0 || collateralDetails !== "N/A") && (
        <div className="flex items-center justify-between bg-gray-50 rounded-lg p-3 mb-4">
          {emi > 0 && (
            <div>
              <span className="text-xs text-krishirin-text-muted">Monthly EMI: </span>
              <span className="font-bold text-krishirin-text">₹{emi.toLocaleString("en-IN")}</span>
            </div>
          )}
          <div className="flex items-center gap-1 text-xs">
            <ShieldCheck className="w-3.5 h-3.5 text-krishirin-success" />
            <span>{collateralRequired ? collateralDetails : "Collateral Waived"}</span>
          </div>
        </div>
      )}

      {/* Harvest-aligned repayment */}
      {schedule.length > 0 && (
        <div>
          <h4 className="text-xs font-medium text-krishirin-text mb-2">Repayment Schedule</h4>
          <div className="space-y-1.5">
            {schedule.map((entry: Record<string, unknown>, i: number) => (
              <div
                key={i}
                className={`flex items-center justify-between text-xs px-3 py-2 rounded-lg ${
                  entry.type === "kharif" ? "bg-green-50" : entry.type === "rabi" ? "bg-amber-50" : "bg-gray-50"
                }`}
              >
                <span className="font-medium">{String(entry.month ?? "")}</span>
                <span>₹{Number(entry.amount ?? 0).toLocaleString("en-IN")}</span>
                <span className="text-krishirin-text-muted">{String(entry.source ?? "")}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {rationale && (
        <p className="text-xs text-krishirin-text-muted mt-3 italic">{rationale}</p>
      )}
    </div>
  );
}
