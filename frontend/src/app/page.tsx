"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { useApplication } from "@/context/ApplicationContext";
import { getPreCallBriefing, getResults, getPipelineStatus } from "@/lib/api";
import type { PreCallBriefing, AllResults } from "@/lib/types";

import CardNav from "@/components/ui/CardNav";
import type { CardNavItem } from "@/components/ui/CardNav";
import RiskFlagCard from "@/components/dashboard/RiskFlagCard";

import {
  Sprout,
  User,
  Shield,
  TrendingUp,
  CheckCircle2,
  Loader2,
} from "lucide-react";

const Grainient = dynamic(() => import("@/components/ui/Grainient"), {
  ssr: false,
});

export default function Dashboard() {
  const router = useRouter();
  const { farmerId, setPhase } = useApplication();
  const [briefing, setBriefing] = useState<PreCallBriefing | null>(null);
  const [results, setLocalResults] = useState<AllResults | null>(null);
  const [pipelineProgress, setPipelineProgress] = useState<number>(0);
  const [pipelineAgents, setPipelineAgents] = useState<string[]>([]);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  const activeFarmerId = farmerId || "";

  // Fetch briefing and results
  const fetchData = useCallback(async () => {
    if (!activeFarmerId) return; // Don't fetch with empty ID
    try {
      const b = await getPreCallBriefing(activeFarmerId);
      setBriefing(b);
    } catch {
      // No briefing available
    }
    try {
      const r = await getResults(activeFarmerId);
      const rAny = r as unknown as Record<string, unknown>;
      // Accept partial results too (agents_done means some data is available)
      if (r && (rAny.pipeline_complete || rAny.agents_done)) {
        setLocalResults(r);
        if (rAny.pipeline_complete) {
          setPipelineRunning(false);
        }
      }
    } catch {
      // No results yet
    }
  }, [activeFarmerId]);

  // Initial load
  useEffect(() => {
    setPhase("apply");
    fetchData();
  }, [activeFarmerId, setPhase, fetchData]);

  // Poll for pipeline status when analysis is running
  useEffect(() => {
    if (!activeFarmerId) return; // Don't poll with empty ID
    async function checkStatus() {
      try {
        const status = await getPipelineStatus(activeFarmerId) as unknown as Record<string, unknown>;
        const progress = (status?.overall_progress as number) ?? 0;
        const agents = (status?.completed_agent_names ?? status?.completed_agents ?? []) as string[];
        const isRunning = status?.status === "running";
        const isComplete = status?.status === "complete";

        setPipelineProgress(progress);
        setPipelineAgents(agents);

        if (isRunning && !pipelineRunning) {
          setPipelineRunning(true);
        }

        // Fetch partial results on every poll while running (shows data as agents complete)
        if (isRunning || isComplete) {
          await fetchData();
        }

        if (isComplete) {
          setPipelineRunning(false);
        }
      } catch {
        // Status endpoint not available yet
      }
    }

    // Start polling
    pollRef.current = setInterval(checkStatus, 3000);
    // Also check immediately
    checkStatus();

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [activeFarmerId, fetchData, pipelineRunning]);

  // Credit assessment from ML scoring agent
  const creditAssessment = (results as unknown as Record<string, unknown>)?.credit_assessment as Record<string, unknown> | undefined;
  const briefingScore = briefing?.score as Record<string, unknown> | undefined;
  // Merge: prefer agent output, fall back to briefing
  const score = (creditAssessment?.grameen_score != null)
    ? creditAssessment
    : briefingScore;

  // Other agent outputs
  const riskAnalysis = (results as unknown as Record<string, unknown>)?.risk_analysis as Record<string, unknown> | undefined;
  const agriAnalysis = (results as unknown as Record<string, unknown>)?.agricultural_analysis as Record<string, unknown> | undefined;
  const gapAnalysis = (results as unknown as Record<string, unknown>)?.gap_analysis as Record<string, unknown> | undefined;
  const clarificationQsRaw = ((results as unknown as Record<string, unknown>)?.clarification_questions ?? []) as unknown[];
  const clarificationQs: string[] = clarificationQsRaw.map((q) =>
    typeof q === "string" ? q : typeof q === "object" && q !== null
      ? String((q as Record<string, unknown>).question ?? (q as Record<string, unknown>).text ?? JSON.stringify(q))
      : String(q)
  );
  const farmerSummaryRaw = (results as unknown as Record<string, unknown>)?.farmer_summary;
  const farmerSummary: string = typeof farmerSummaryRaw === "string"
    ? farmerSummaryRaw
    : farmerSummaryRaw && typeof farmerSummaryRaw === "object"
      ? Object.entries(farmerSummaryRaw as Record<string, unknown>)
          .map(([k, v]) => `${k}: ${typeof v === "object" ? JSON.stringify(v) : String(v)}`)
          .join(" · ")
      : "";

  const farmer = briefing?.farmer;

  // CardNav configuration
  const navItems: CardNavItem[] = [
    {
      label: "Saarkshep",
      bgColor: "#1B5E20",
      textColor: "#fff",
      links: [
        { label: "Dashboard", ariaLabel: "Go to Dashboard", onClick: () => window.scrollTo({ top: 0, behavior: "smooth" }) },
      ],
    },
    {
      label: "Salah",
      bgColor: "#2E7D32",
      textColor: "#fff",
      links: [
        { label: "Start Call", ariaLabel: "Start Advisory Call", onClick: () => router.push("/call/advisory") },
        { label: "View Results", ariaLabel: "View Results", onClick: () => router.push("/summary") },
      ],
    },
    {
      label: "Dastavez",
      bgColor: "#388E3C",
      textColor: "#fff",
      links: [
        { label: "Upload Docs", ariaLabel: "Upload Documents", onClick: () => router.push("/profile") },
        { label: "Profile", ariaLabel: "View Profile", onClick: () => router.push("/profile") },
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-krishirin-bg">
      {/* ============ GRAINIENT HERO HEADER ============ */}
      <header className="relative overflow-hidden">
        <div className="absolute inset-0 opacity-50">
          <Grainient
            color1="#1B5E20"
            color2="#FF6F00"
            color3="#FAFDF6"
            timeSpeed={0.12}
            grainAmount={0.04}
            contrast={1.15}
            saturation={0.9}
            warpSpeed={1.5}
            warpAmplitude={60}
            zoom={1.0}
          />
        </div>
        <div className="relative z-10 max-w-6xl mx-auto px-4 pt-6 pb-10">
          {/* Top Bar */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3.5">
              <div className="w-11 h-11 rounded-xl bg-white/20 backdrop-blur-md flex items-center justify-center border border-white/15">
                <Sprout className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-[22px] font-extrabold text-white tracking-[-0.04em] leading-none">
                  Artha Setu
                </h1>
                <p className="text-[10px] text-white/50 tracking-[0.14em] uppercase font-medium mt-0.5">
                  अर्थ सेतु
                </p>
              </div>
            </div>
            <button
              onClick={() => router.push("/profile")}
              className="flex items-center gap-2 px-4 py-2.5 bg-white/12 hover:bg-white/20 backdrop-blur-md rounded-xl transition-all border border-white/10"
            >
              <User className="w-4 h-4 text-white/80" />
              <span className="text-sm font-medium text-white/90">Profile</span>
            </button>
          </div>

          {/* Brand Tagline */}
          <div className="animate-stagger-1 mb-6">
            <p className="tagline-hindi text-white/90">
              Fasal badhe, karz ghate
            </p>
            <p className="text-[13px] text-white/50 font-light tracking-wide mt-1">
              Crops grow, debts shrink.
            </p>
          </div>

          {/* Farmer Greeting */}
          {farmer?.name && (
            <div className="animate-stagger-2">
              <h2 className="text-2xl font-bold text-white tracking-tight">
                Namaste, {farmer.name} ji
              </h2>
              <p className="text-sm text-white/70 mt-1 font-light">
                {[farmer.district, farmer.state].filter(Boolean).join(", ")}
                {farmer.land_holding_acres ? ` · ${farmer.land_holding_acres} acres` : ""}
                {farmer.land_type ? ` (${farmer.land_type})` : ""}
                {farmer.crops?.length ? ` · ${farmer.crops.join(", ")}` : ""}
              </p>
            </div>
          )}
        </div>
      </header>

      {/* ============ CARD NAV ============ */}
      <div className="max-w-6xl mx-auto px-4 -mt-4 mb-6 animate-stagger-2">
        <CardNav
          items={navItems}
          logoContent={
            <div className="flex items-center gap-2">
              <Sprout className="w-5 h-5 text-krishirin-primary" />
              <span className="font-extrabold text-krishirin-primary text-sm tracking-[-0.03em]">
                Artha Setu
              </span>
            </div>
          }
          baseColor="#FAFDF6"
          menuColor="#1B5E20"
          buttonBgColor="#1B5E20"
          buttonTextColor="#fff"
          ctaLabel="Call Shuru Karein"
          onCtaClick={() => router.push("/call/advisory")}
        />
      </div>

      <div className="max-w-6xl mx-auto px-4 space-y-8 pb-16">
        {/* ============ HERO METRICS ROW ============ */}
        {/* Pipeline Progress Indicator */}
        {pipelineRunning && (
          <div className="glass-card rounded-2xl p-6 animate-stagger-3">
            <div className="flex items-center gap-3 mb-4">
              <Loader2 className="w-5 h-5 text-krishirin-primary animate-spin" />
              <h3 className="font-semibold text-krishirin-text">Analyzing your profile...</h3>
              <span className="ml-auto text-sm font-medium text-krishirin-primary">{pipelineProgress}%</span>
            </div>
            <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden mb-3">
              <div
                className="h-full bg-krishirin-primary rounded-full transition-all duration-500"
                style={{ width: `${pipelineProgress}%` }}
              />
            </div>
            {pipelineAgents.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {pipelineAgents.map((agent) => (
                  <span key={agent} className="inline-flex items-center gap-1 px-2.5 py-1 bg-krishirin-success/10 text-krishirin-success text-xs font-medium rounded-full">
                    <CheckCircle2 className="w-3 h-3" />
                    {agent}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}


        {/* ============ JOKHIM SUCHNA — RISK FLAGS ============ */}
        {Array.isArray(briefing?.flags) && briefing.flags.length > 0 && (
          <div className="animate-stagger-5">
            <div className="section-header">
              <h2>जोखिम सूचना</h2>
              <p>Risk Alerts — Identified from your documents and data</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {briefing.flags.map((flag, i) => {
                // Normalize flag structure — agent may return different formats
                const f = typeof flag === "string"
                  ? { type: "info" as const, category: "Alert", description: flag, detail: "" }
                  : { type: (flag.type || "info") as "warning" | "critical" | "info", category: flag.category || "Alert", description: flag.description || flag.detail || JSON.stringify(flag), detail: flag.detail || "" };
                return <RiskFlagCard key={i} flag={f} />;
              })}
            </div>
          </div>
        )}

        {/* ============ SCORE KAARAK — SCORE FACTORS ============ */}
        {score && ("top_positive_factors" in score || "top_negative_factors" in score) && (
          <div className="animate-stagger-6">
            <div className="section-header">
              <h2>स्कोर कारक</h2>
              <p>Score Factors — What drives your Grameen Score</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Strengths */}
              <div className="glass-card rounded-2xl p-5">
                <h4 className="text-xs font-semibold text-krishirin-success uppercase tracking-wider mb-3 flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5" /> Strengths
                </h4>
                <div className="space-y-2">
                  {(("top_positive_factors" in score ? score.top_positive_factors : []) as unknown[])?.map((f: unknown, i: number) => (
                    <div key={i} className="flex items-start gap-2.5">
                      <div className="w-2 h-2 rounded-full bg-krishirin-success mt-1.5 shrink-0" />
                      <span className="text-sm text-krishirin-text leading-snug">{typeof f === "string" ? f : JSON.stringify(f)}</span>
                    </div>
                  ))}
                </div>
              </div>
              {/* Risks */}
              <div className="glass-card rounded-2xl p-5">
                <h4 className="text-xs font-semibold text-krishirin-danger uppercase tracking-wider mb-3 flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5" /> Flags & Risks
                </h4>
                <div className="space-y-2">
                  {(("top_negative_factors" in score ? score.top_negative_factors : []) as unknown[])?.map((f: unknown, i: number) => (
                    <div key={i} className="flex items-start gap-2.5">
                      <div className="w-2 h-2 rounded-full bg-krishirin-danger mt-1.5 shrink-0" />
                      <span className="text-sm text-krishirin-text leading-snug">{typeof f === "string" ? f : JSON.stringify(f)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ============ PRE-CALL ANALYSIS RESULTS ============ */}

        {/* ---- RISK ANALYSIS ---- */}
        {riskAnalysis && Object.keys(riskAnalysis).length > 0 && (
          <div className="animate-stagger-7">
            <div className="section-header">
              <h2>जोखिम विश्लेषण</h2>
              <p>Risk Analysis — Identified risks and their severity</p>
            </div>
            <div className="glass-card rounded-2xl p-5">
              {/* Critical risks */}
              {Array.isArray(riskAnalysis.critical_risks ?? riskAnalysis.critical_flags) &&
                ((riskAnalysis.critical_risks ?? riskAnalysis.critical_flags) as unknown[]).length > 0 && (
                <div className="mb-4">
                  <h4 className="text-xs font-semibold text-krishirin-danger uppercase tracking-wider mb-2">Critical Risks</h4>
                  {((riskAnalysis.critical_risks ?? riskAnalysis.critical_flags) as unknown[]).map((r, i) => (
                    <div key={i} className="flex items-start gap-2 text-sm text-krishirin-text mb-2 bg-red-50 rounded-lg p-2.5">
                      <div className="w-2 h-2 rounded-full bg-krishirin-danger mt-1.5 shrink-0" />
                      <span>{typeof r === "string" ? r : String((r as Record<string, unknown>).detail ?? (r as Record<string, unknown>).description ?? JSON.stringify(r))}</span>
                    </div>
                  ))}
                </div>
              )}
              {/* Warnings */}
              {Array.isArray(riskAnalysis.warnings ?? riskAnalysis.warning_flags) &&
                ((riskAnalysis.warnings ?? riskAnalysis.warning_flags) as unknown[]).length > 0 && (
                <div className="mb-4">
                  <h4 className="text-xs font-semibold text-amber-600 uppercase tracking-wider mb-2">Warnings</h4>
                  {((riskAnalysis.warnings ?? riskAnalysis.warning_flags) as unknown[]).map((w, i) => (
                    <div key={i} className="flex items-start gap-2 text-sm text-krishirin-text mb-2 bg-amber-50 rounded-lg p-2.5">
                      <div className="w-2 h-2 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                      <span>{typeof w === "string" ? w : String((w as Record<string, unknown>).detail ?? (w as Record<string, unknown>).description ?? JSON.stringify(w))}</span>
                    </div>
                  ))}
                </div>
              )}
              {/* Actionable insights */}
              {Array.isArray(riskAnalysis.actionable_insights) && (riskAnalysis.actionable_insights as unknown[]).length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-krishirin-success uppercase tracking-wider mb-2">Actionable Steps</h4>
                  {(riskAnalysis.actionable_insights as unknown[]).map((a, i) => (
                    <div key={i} className="flex items-start gap-2 text-sm text-krishirin-text mb-2 bg-green-50 rounded-lg p-2.5">
                      <div className="w-2 h-2 rounded-full bg-krishirin-success mt-1.5 shrink-0" />
                      <span>{typeof a === "string" ? a : String((a as Record<string, unknown>).action ?? JSON.stringify(a))}</span>
                    </div>
                  ))}
                </div>
              )}
              {/* Overall risk score */}
              {riskAnalysis.overall_risk_score != null && (
                <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between">
                  <span className="text-sm text-krishirin-text-muted">Overall Risk Score</span>
                  <span className={`text-lg font-bold ${Number(riskAnalysis.overall_risk_score) > 60 ? "text-krishirin-danger" : Number(riskAnalysis.overall_risk_score) > 30 ? "text-amber-600" : "text-krishirin-success"}`}>
                    {String(riskAnalysis.overall_risk_score)}/100
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ---- AGRICULTURAL & MARKET ANALYSIS ---- */}
        {agriAnalysis && Object.keys(agriAnalysis).length > 0 ? (
          <div>
            <div className="section-header">
              <h2>कृषि और बाज़ार विश्लेषण</h2>
              <p>Agricultural & Market Analysis — Crop outlook, weather, and market trends</p>
            </div>
            <div className="glass-card rounded-2xl p-5 space-y-4">
              {agriAnalysis.market_trend_summary ? (
                <div className="bg-blue-50 rounded-lg p-4">
                  <h4 className="text-xs font-semibold text-blue-700 uppercase tracking-wider mb-2 flex items-center gap-1">
                    <TrendingUp className="w-3.5 h-3.5" /> Market Outlook
                  </h4>
                  <p className="text-sm text-krishirin-text">{String(agriAnalysis.market_trend_summary)}</p>
                </div>
              ) : null}
              {Array.isArray(agriAnalysis.current_market_prices ?? agriAnalysis.yield_predictions) ? (
                <div>
                  <h4 className="text-xs font-semibold text-krishirin-text uppercase tracking-wider mb-2">Crop Predictions</h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-krishirin-border">
                          <th className="text-left py-2 px-2 font-medium text-krishirin-text-muted">Crop</th>
                          <th className="text-right py-2 px-2 font-medium text-krishirin-text-muted">Price/Yield</th>
                          <th className="text-right py-2 px-2 font-medium text-krishirin-text-muted">Trend</th>
                        </tr>
                      </thead>
                      <tbody>
                        {((agriAnalysis.current_market_prices ?? agriAnalysis.yield_predictions ?? []) as unknown[]).map((item: unknown, i: number) => {
                          const p = item as Record<string, unknown>;
                          return (
                            <tr key={i} className="border-b border-gray-50">
                              <td className="py-2 px-2 font-medium">{String(p.crop ?? p.commodity ?? "")}</td>
                              <td className="py-2 px-2 text-right">₹{String(p.ml_predicted_price ?? p.predicted_yield_kg_per_ha ?? p.msp_price ?? "")}</td>
                              <td className="py-2 px-2 text-right">
                                <span className={`text-xs px-1.5 py-0.5 rounded ${String(p.price_trend ?? p.trend) === "increasing" ? "bg-green-100 text-green-700" : String(p.price_trend ?? p.trend) === "decreasing" ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-600"}`}>
                                  {String(p.price_trend ?? p.trend ?? "")}
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : null}
              {(agriAnalysis.weather_advisory || agriAnalysis.weather_assessment) ? (
                <div className="bg-cyan-50 rounded-lg p-4">
                  <h4 className="text-xs font-semibold text-cyan-700 uppercase tracking-wider mb-2">Weather Advisory</h4>
                  <p className="text-sm text-krishirin-text">{String(agriAnalysis.weather_advisory ?? agriAnalysis.weather_assessment)}</p>
                </div>
              ) : null}
            </div>
          </div>
        ) : null}

        {/* ---- GAP ANALYSIS & ACTIONABLE INSIGHTS ---- */}
        {gapAnalysis && Object.keys(gapAnalysis).length > 0 && (
          <div>
            <div className="section-header">
              <h2>कमी विश्लेषण</h2>
              <p>Gap Analysis & Actionable Insights</p>
            </div>
            <div className="glass-card rounded-2xl p-5">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${gapAnalysis.application_ready ? "bg-krishirin-success" : "bg-krishirin-warning"}`} />
                  <span className="font-semibold text-sm">
                    {gapAnalysis.application_ready ? "Ready for Loan Application" : "Improvements Needed"}
                  </span>
                </div>
                <span className="text-sm font-bold text-krishirin-primary">
                  {String(gapAnalysis.readiness_score ?? 0)}% readiness
                </span>
              </div>
              <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden mb-4">
                <div
                  className="h-full rounded-full bg-krishirin-primary transition-all duration-1000"
                  style={{ width: `${Number(gapAnalysis.readiness_score ?? 0)}%` }}
                />
              </div>
              {Array.isArray(gapAnalysis.critical_gaps) && (gapAnalysis.critical_gaps as unknown[]).length > 0 && (
                <div className="mb-3">
                  <h4 className="text-xs font-semibold text-krishirin-danger uppercase tracking-wider mb-2">Critical Issues</h4>
                  {(gapAnalysis.critical_gaps as unknown[]).map((g, i) => (
                    <div key={i} className="flex items-start gap-2 text-sm text-krishirin-text mb-1.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-krishirin-danger mt-2 shrink-0" />
                      <span>{typeof g === "string" ? g : String((g as Record<string, unknown>).detail ?? (g as Record<string, unknown>).issue ?? JSON.stringify(g))}</span>
                    </div>
                  ))}
                </div>
              )}
              {Array.isArray(gapAnalysis.improvement_suggestions) && (gapAnalysis.improvement_suggestions as unknown[]).length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-krishirin-success uppercase tracking-wider mb-2">Actionable Steps</h4>
                  {(gapAnalysis.improvement_suggestions as unknown[]).map((s, i) => (
                    <div key={i} className="flex items-start gap-2 text-sm text-krishirin-text mb-1.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-krishirin-success mt-2 shrink-0" />
                      <span>{typeof s === "string" ? s : String((s as Record<string, unknown>).suggestion ?? (s as Record<string, unknown>).action ?? JSON.stringify(s))}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ---- CLARIFICATION QUESTIONS ---- */}
        {clarificationQs.length > 0 && (
          <div>
            <div className="section-header">
              <h2>स्पष्टीकरण प्रश्न</h2>
              <p>Questions for the Advisory Call — To clarify during conversation</p>
            </div>
            <div className="glass-card rounded-2xl p-5">
              <div className="space-y-3">
                {clarificationQs.map((q, i) => (
                  <div key={i} className="flex items-start gap-3 bg-blue-50 rounded-lg p-3">
                    <span className="w-6 h-6 rounded-full bg-krishirin-primary text-white text-xs flex items-center justify-center shrink-0 mt-0.5">
                      {i + 1}
                    </span>
                    <span className="text-sm text-krishirin-text">{typeof q === "string" ? q : JSON.stringify(q)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ---- FARMER SUMMARY ---- */}
        {farmerSummary && (
          <div>
            <div className="section-header">
              <h2>किसान सारांश</h2>
              <p>Farmer Summary — Overall assessment</p>
            </div>
            <div className="glass-card rounded-2xl p-5">
              <p className="text-sm text-krishirin-text leading-relaxed">{farmerSummary}</p>
            </div>
          </div>
        )}

        {/* ============ FOOTER ============ */}
        <div className="pt-4 border-t border-krishirin-border">
          <p className="text-xs text-krishirin-text-muted text-center">
            Artha Setu &middot; Powered by Databricks &middot; Data: ICRISAT, data.gov.in &middot; ML: Spark MLlib + MLflow
          </p>
        </div>
      </div>
    </div>
  );
}
