"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { GrameenScoreCard } from "@/components/results/GrameenScoreCard";
import { useApplication } from "@/context/ApplicationContext";
import { getPipelineStatus, getResults } from "@/lib/api";
import type { AgentPipelineStatus, AgentName, AllResults } from "@/lib/types";
import {
  CheckCircle2,
  Loader2,
  Clock,
  AlertCircle,
  Brain,
  ArrowRight,
} from "lucide-react";

const AGENT_LABELS: Record<AgentName, { label: string; desc: string }> = {
  EligibilityChecker: { label: "Eligibility Checker", desc: "Finding eligible government schemes" },
  GrameenScorer: { label: "Grameen Scorer", desc: "Explaining credit score factors" },
  GapAnalyzer: { label: "Gap Analyzer", desc: "Identifying missing documents & risks" },
  StrategyArchitect: { label: "Strategy Architect", desc: "Designing optimal loan package" },
  AgriAdvisor: { label: "Agricultural Advisor", desc: "Building farming & repayment plan" },
};

// Mock data for demo
const MOCK_PIPELINE: AgentPipelineStatus = {
  agents: [
    { name: "EligibilityChecker", status: "completed" },
    { name: "GrameenScorer", status: "completed" },
    { name: "GapAnalyzer", status: "running" },
    { name: "StrategyArchitect", status: "pending" },
    { name: "AgriAdvisor", status: "pending" },
  ],
  overall_progress: 45,
};

export default function ProcessingPage() {
  const router = useRouter();
  const { farmerId, setPhase, setResults } = useApplication();
  const [pipeline, setPipeline] = useState<AgentPipelineStatus>(MOCK_PIPELINE);
  const [results, setLocalResults] = useState<AllResults | null>(null);
  const [demoStep, setDemoStep] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const activeFarmerId = farmerId || "";

  useEffect(() => {
    setPhase("processing");
  }, [setPhase]);

  // Demo: simulate agent progress
  useEffect(() => {
    const agentOrder: AgentName[] = [
      "EligibilityChecker",
      "GrameenScorer",
      "GapAnalyzer",
      "StrategyArchitect",
      "AgriAdvisor",
    ];

    intervalRef.current = setInterval(() => {
      setDemoStep((prev) => {
        const next = prev + 1;
        if (next > agentOrder.length * 2) {
          if (intervalRef.current) clearInterval(intervalRef.current);
          return prev;
        }

        const agentIndex = Math.floor(next / 2);
        const isRunning = next % 2 === 1;

        setPipeline((p) => ({
          ...p,
          agents: p.agents.map((a, i) => ({
            ...a,
            status:
              i < agentIndex
                ? "completed"
                : i === agentIndex
                  ? isRunning
                    ? "running"
                    : "completed"
                  : "pending",
          })),
          overall_progress: Math.min(100, Math.round(((agentIndex + (isRunning ? 0.5 : 1)) / agentOrder.length) * 100)),
        }));

        return next;
      });
    }, 1500);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  // Also try real API
  useEffect(() => {
    const poll = setInterval(async () => {
      try {
        const status = await getPipelineStatus(activeFarmerId);
        setPipeline(status);
        if (status.overall_progress === 100) {
          clearInterval(poll);
          const res = await getResults(activeFarmerId);
          setLocalResults(res);
          setResults(res);
        }
      } catch {
        // Use demo pipeline
      }
    }, 3000);

    return () => clearInterval(poll);
  }, [activeFarmerId, setResults]);

  const allComplete = pipeline.agents.every((a) => a.status === "completed");

  return (
    <div>
      <div className="max-w-3xl mx-auto p-6 space-y-6">
        <div className="text-center mb-2">
          <h1 className="text-xl font-bold text-krishirin-text flex items-center justify-center gap-2">
            <Brain className="w-6 h-6 text-krishirin-primary" />
            Agent Pipeline Processing
          </h1>
          <p className="text-sm text-krishirin-text-muted mt-1">
            Our AI agents are analyzing your data and creating your loan strategy
          </p>
        </div>

        {/* Progress bar */}
        <div className="bg-gray-100 rounded-full h-3 overflow-hidden">
          <div
            className="bg-krishirin-primary h-full rounded-full transition-all duration-700"
            style={{ width: `${pipeline.overall_progress}%` }}
          />
        </div>
        <p className="text-center text-sm text-krishirin-text-muted">
          {pipeline.overall_progress}% complete
        </p>

        {/* Agent cards */}
        <div className="space-y-3">
          {pipeline.agents.map((agent) => {
            const info = AGENT_LABELS[agent.name];
            return (
              <div
                key={agent.name}
                className={`flex items-center gap-4 rounded-xl border p-4 transition-colors ${
                  agent.status === "completed"
                    ? "border-green-200 bg-green-50"
                    : agent.status === "running"
                      ? "border-blue-200 bg-blue-50"
                      : agent.status === "error"
                        ? "border-red-200 bg-red-50"
                        : "border-gray-200 bg-gray-50"
                }`}
              >
                <div className="shrink-0">
                  {agent.status === "completed" && (
                    <CheckCircle2 className="w-6 h-6 text-krishirin-success" />
                  )}
                  {agent.status === "running" && (
                    <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
                  )}
                  {agent.status === "pending" && (
                    <Clock className="w-6 h-6 text-gray-400" />
                  )}
                  {agent.status === "error" && (
                    <AlertCircle className="w-6 h-6 text-red-500" />
                  )}
                </div>
                <div className="flex-1">
                  <div className="font-medium text-sm text-krishirin-text">
                    {info.label}
                  </div>
                  <div className="text-xs text-krishirin-text-muted">
                    {agent.status === "running" ? `${info.desc}...` : info.desc}
                  </div>
                </div>
                <span
                  className={`text-xs font-medium px-2 py-1 rounded-full ${
                    agent.status === "completed"
                      ? "bg-green-100 text-green-700"
                      : agent.status === "running"
                        ? "bg-blue-100 text-blue-700"
                        : "bg-gray-100 text-gray-500"
                  }`}
                >
                  {agent.status === "completed"
                    ? "Done"
                    : agent.status === "running"
                      ? "Running..."
                      : agent.status === "error"
                        ? "Error"
                        : "Pending"}
                </span>
              </div>
            );
          })}
        </div>

        {/* Results preview when available */}
        {results?.score && (
          <GrameenScoreCard score={results.score} />
        )}

        {/* Continue button */}
        {allComplete && (
          <div className="text-center pt-4">
            <button
              onClick={() => router.push("/call/advisory")}
              className="inline-flex items-center gap-2 px-8 py-3 bg-krishirin-primary text-white rounded-lg font-medium hover:bg-krishirin-primary/90 transition-colors"
            >
              Proceed to Advisory Call
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
