"use client";

import type { PreCallBriefing as PreCallBriefingData } from "@/lib/types";
import {
  AlertTriangle,
  ShieldCheck,
  ShieldAlert,
  Info,
  HelpCircle,
} from "lucide-react";

interface PreCallBriefingProps {
  data: PreCallBriefingData | null;
  loading?: boolean;
}

export function PreCallBriefing({ data, loading }: PreCallBriefingProps) {
  if (loading) {
    return (
      <div className="p-4 space-y-3">
        <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4" />
        <div className="h-4 bg-gray-200 rounded animate-pulse w-1/2" />
        <div className="h-4 bg-gray-200 rounded animate-pulse w-2/3" />
      </div>
    );
  }

  if (!data) return null;

  const { score, flags, auto_questions } = data;

  const riskColor = {
    A: "text-krishirin-success",
    B: "text-krishirin-warning",
    C: "text-orange-600",
    D: "text-krishirin-danger",
  }[score.risk_category];

  return (
    <div className="flex flex-col h-full overflow-auto transcript-scroll">
      <div className="px-3 py-2 border-b border-krishirin-border">
        <h3 className="text-sm font-semibold text-krishirin-text">
          Pre-Call Briefing
        </h3>
      </div>

      <div className="p-3 space-y-4 text-sm">
        {/* Grameen Score */}
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-krishirin-text-muted font-medium">
              Grameen Score
            </span>
            <span className={`text-2xl font-bold ${riskColor}`}>
              {score.grameen_score}
              <span className="text-sm">/100</span>
            </span>
          </div>
          <div className="flex items-center gap-2">
            {score.risk_category === "A" || score.risk_category === "B" ? (
              <ShieldCheck className="w-4 h-4 text-krishirin-success" />
            ) : (
              <ShieldAlert className="w-4 h-4 text-krishirin-warning" />
            )}
            <span className={`font-medium ${riskColor}`}>
              Risk: {score.risk_category} (
              {
                { A: "Low", B: "Moderate", C: "Elevated", D: "High" }[
                  score.risk_category
                ]
              }
              )
            </span>
          </div>
          <div className="mt-2 text-xs text-krishirin-text-muted">
            Capacity: ₹{(score.predicted_capacity / 1000).toFixed(0)}K |
            Repayment: {(score.repayment_prob * 100).toFixed(0)}%
          </div>
        </div>

        {/* Flags */}
        {flags.length > 0 && (
          <div>
            <h4 className="font-medium text-krishirin-text mb-2 flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5 text-krishirin-warning" />
              Flags
            </h4>
            <div className="space-y-1.5">
              {flags.map((flag, i) => (
                <div
                  key={i}
                  className={`px-2.5 py-1.5 rounded text-xs ${
                    flag.type === "critical"
                      ? "bg-red-50 text-red-700 border border-red-200"
                      : flag.type === "warning"
                        ? "bg-amber-50 text-amber-700 border border-amber-200"
                        : "bg-blue-50 text-blue-700 border border-blue-200"
                  }`}
                >
                  <span className="font-medium">{flag.category}:</span>{" "}
                  {flag.description}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Auto Questions */}
        {auto_questions.length > 0 && (
          <div>
            <h4 className="font-medium text-krishirin-text mb-2 flex items-center gap-1">
              <HelpCircle className="w-3.5 h-3.5 text-krishirin-info" />
              Questions to Verify
            </h4>
            <ol className="space-y-1.5 list-decimal list-inside">
              {auto_questions.map((q, i) => (
                <li key={i} className="text-xs text-krishirin-text-muted">
                  {q}
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* Positive Factors */}
        <div>
          <h4 className="font-medium text-krishirin-text mb-1 flex items-center gap-1">
            <Info className="w-3.5 h-3.5 text-krishirin-success" />
            Strengths
          </h4>
          <ul className="space-y-1">
            {score.top_positive_factors.map((f, i) => (
              <li
                key={i}
                className="text-xs text-krishirin-success flex items-center gap-1"
              >
                + {f}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
