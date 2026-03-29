"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { GrameenScoreCard } from "@/components/results/GrameenScoreCard";
import { LoanStrategyCard } from "@/components/results/LoanStrategyCard";
import { SchemeEligibilityCard } from "@/components/results/SchemeEligibility";
import { AgriAdvisoryCard } from "@/components/results/AgriAdvisoryCard";
import { RepaymentCashflow } from "@/components/results/RepaymentCashflow";
import { useApplication } from "@/context/ApplicationContext";
import { getResults } from "@/lib/api";
import type { AllResults } from "@/lib/types";
import {
  CheckCircle2,
  Download,
  RotateCcw,
  Sprout,
} from "lucide-react";

export default function SummaryPage() {
  const router = useRouter();
  const { results, farmerId, setPhase, setResults, reset } = useApplication();
  const [fetchedResults, setFetchedResults] = useState<AllResults | null>(null);

  useEffect(() => {
    setPhase("summary");
  }, [setPhase]);

  // If context has no results (e.g. page refresh), try fetching from backend
  useEffect(() => {
    if (!results && farmerId) {
      getResults(farmerId)
        .then((r) => {
          setFetchedResults(r);
          setResults(r);
        })
        .catch(() => {
          // No results available — will show empty state
        });
    }
  }, [results, farmerId, setResults]);

  const displayResults = results || fetchedResults;

  const handleNewApplication = () => {
    reset();
    router.push("/");
  };

  return (
    <div>
      <div className="max-w-4xl mx-auto p-6 space-y-6 pb-20">
        {/* Success header */}
        <div className="text-center bg-green-50 rounded-2xl p-6 border border-green-200">
          <div className="flex justify-center mb-3">
            <div className="w-16 h-16 rounded-full bg-krishirin-success/10 flex items-center justify-center">
              <CheckCircle2 className="w-10 h-10 text-krishirin-success" />
            </div>
          </div>
          <h1 className="text-2xl font-bold text-krishirin-text mb-1">
            Advisory Complete
          </h1>
          <p className="text-sm text-krishirin-text-muted">
            Both calls are finished. Here is the complete loan advisory summary.
          </p>
        </div>

        {displayResults ? (
          <>
            <GrameenScoreCard score={displayResults.score} />
            <LoanStrategyCard strategy={displayResults.loan_strategy} />
            <SchemeEligibilityCard schemes={displayResults.schemes} />
            <AgriAdvisoryCard advisory={displayResults.agri_advisory} />
            <RepaymentCashflow
              cashflow={displayResults.agri_advisory?.repayment_cashflow_map}
            />
          </>
        ) : (
          <div className="text-center py-12 text-krishirin-text-muted">
            <Sprout className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>No results available. Complete the full advisory flow first.</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-center gap-4 pt-4">
          <button
            onClick={handleNewApplication}
            className="flex items-center gap-2 px-6 py-3 border border-krishirin-border rounded-lg text-sm font-medium text-krishirin-text hover:bg-gray-50"
          >
            <RotateCcw className="w-4 h-4" />
            New Application
          </button>
          <button className="flex items-center gap-2 px-6 py-3 bg-krishirin-primary text-white rounded-lg text-sm font-medium hover:bg-krishirin-primary/90">
            <Download className="w-4 h-4" />
            Download Report
          </button>
        </div>
      </div>
    </div>
  );
}
