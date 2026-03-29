"use client";

import type { GrameenScore } from "@/lib/types";
import { ShieldCheck, ShieldAlert, TrendingUp, TrendingDown } from "lucide-react";

interface GrameenScoreCardProps {
  score: GrameenScore;
}

export function GrameenScoreCard({ score }: GrameenScoreCardProps) {
  const riskConfig = {
    A: { label: "Low Risk", color: "text-krishirin-success", bg: "bg-green-50", border: "border-green-200" },
    B: { label: "Moderate Risk", color: "text-krishirin-warning", bg: "bg-amber-50", border: "border-amber-200" },
    C: { label: "Elevated Risk", color: "text-orange-600", bg: "bg-orange-50", border: "border-orange-200" },
    D: { label: "High Risk", color: "text-krishirin-danger", bg: "bg-red-50", border: "border-red-200" },
  }[score.risk_category];

  const gaugePercent = score.grameen_score;

  return (
    <div className={`rounded-xl border ${riskConfig.border} ${riskConfig.bg} p-5`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-krishirin-text">Grameen Credit Score</h3>
        {score.risk_category <= "B" ? (
          <ShieldCheck className={`w-5 h-5 ${riskConfig.color}`} />
        ) : (
          <ShieldAlert className={`w-5 h-5 ${riskConfig.color}`} />
        )}
      </div>

      {/* Score gauge */}
      <div className="flex items-end gap-4 mb-4">
        <div className={`text-5xl font-bold ${riskConfig.color}`}>
          {score.grameen_score}
        </div>
        <div className="pb-1">
          <div className="text-sm text-krishirin-text-muted">/100</div>
          <div className={`text-sm font-medium ${riskConfig.color}`}>
            {score.risk_category} — {riskConfig.label}
          </div>
        </div>
      </div>

      {/* Progress bar */}
      <div className="w-full h-3 bg-gray-200 rounded-full mb-4 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-1000 ${
            score.risk_category === "A"
              ? "bg-krishirin-success"
              : score.risk_category === "B"
                ? "bg-krishirin-warning"
                : score.risk_category === "C"
                  ? "bg-orange-500"
                  : "bg-krishirin-danger"
          }`}
          style={{ width: `${gaugePercent}%` }}
        />
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-3 gap-3 text-center mb-4">
        <div className="bg-white/60 rounded-lg p-2">
          <div className="text-xs text-krishirin-text-muted">Repayment</div>
          <div className="text-sm font-bold">
            {(score.repayment_prob * 100).toFixed(0)}%
          </div>
        </div>
        <div className="bg-white/60 rounded-lg p-2">
          <div className="text-xs text-krishirin-text-muted">Cluster</div>
          <div className="text-sm font-bold">{score.risk_cluster}</div>
        </div>
        <div className="bg-white/60 rounded-lg p-2">
          <div className="text-xs text-krishirin-text-muted">Capacity</div>
          <div className="text-sm font-bold">
            ₹{(score.predicted_capacity / 1000).toFixed(0)}K
          </div>
        </div>
      </div>

      {/* Factors */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <h4 className="text-xs font-medium text-krishirin-success mb-1 flex items-center gap-1">
            <TrendingUp className="w-3 h-3" /> Strengths
          </h4>
          {score.top_positive_factors.map((f, i) => (
            <p key={i} className="text-xs text-krishirin-text-muted mb-0.5">
              + {f}
            </p>
          ))}
        </div>
        <div>
          <h4 className="text-xs font-medium text-krishirin-danger mb-1 flex items-center gap-1">
            <TrendingDown className="w-3 h-3" /> Risks
          </h4>
          {score.top_negative_factors.map((f, i) => (
            <p key={i} className="text-xs text-krishirin-text-muted mb-0.5">
              - {f}
            </p>
          ))}
        </div>
      </div>
    </div>
  );
}
