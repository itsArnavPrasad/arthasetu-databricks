"use client";

import type { SchemeEligibility as SchemeEligibilityType } from "@/lib/types";
import { CheckCircle2, XCircle, Award } from "lucide-react";

interface SchemeEligibilityProps {
  schemes: SchemeEligibilityType[];
}

export function SchemeEligibilityCard({ schemes }: SchemeEligibilityProps) {
  return (
    <div className="rounded-xl border border-krishirin-border bg-krishirin-surface p-5">
      <h3 className="font-semibold text-krishirin-text mb-4 flex items-center gap-2">
        <Award className="w-5 h-5 text-krishirin-secondary" />
        Government Scheme Eligibility
      </h3>

      <div className="space-y-3">
        {schemes.map((scheme, i) => (
          <div
            key={i}
            className={`rounded-lg border p-3 ${
              scheme.eligible
                ? "border-green-200 bg-green-50"
                : "border-gray-200 bg-gray-50"
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                {scheme.eligible ? (
                  <CheckCircle2 className="w-4 h-4 text-krishirin-success" />
                ) : (
                  <XCircle className="w-4 h-4 text-gray-400" />
                )}
                <span className="font-medium text-sm">{scheme.scheme_name}</span>
              </div>
              {scheme.eligible && (
                <span className="text-xs font-bold text-krishirin-success">
                  {scheme.match_percent}% match
                </span>
              )}
            </div>
            {scheme.eligible && (
              <div className="ml-6 text-xs text-krishirin-text-muted">
                <p>Benefit: {scheme.benefit_amount}</p>
                <p className="mt-0.5">{scheme.details}</p>
              </div>
            )}
            {!scheme.eligible && scheme.missing_requirements.length > 0 && (
              <div className="ml-6 text-xs text-krishirin-text-muted">
                Missing: {scheme.missing_requirements.join(", ")}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
