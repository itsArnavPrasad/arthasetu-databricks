"use client";

import { Sprout, Cloud, TrendingUp, Coins, Calendar } from "lucide-react";

interface AgriAdvisoryCardProps {
  advisory: Record<string, unknown>;
}

export function AgriAdvisoryCard({ advisory }: AgriAdvisoryCardProps) {
  if (!advisory || typeof advisory !== "object") return null;

  const a = advisory as Record<string, unknown>;
  const landAssessment = (a.land_assessment ?? "") as string;
  const sowingPlan = Array.isArray(a.sowing_plan) ? a.sowing_plan : [];
  const inputCost = (a.input_cost_guidance ?? a.input_costs ?? "") as string;
  const weather = (a.weather_guidance ?? a.weather_advisory ?? "") as string;
  const market = (a.market_timing ?? a.market_trend_summary ?? "") as string;
  const diversification = (a.income_diversification ?? "") as string;

  // If no structured data, show raw JSON
  const hasContent = landAssessment || sowingPlan.length > 0 || inputCost || weather || market;
  if (!hasContent) {
    return (
      <div className="rounded-xl border border-krishirin-border bg-krishirin-surface p-5">
        <h3 className="font-semibold text-krishirin-text mb-3 flex items-center gap-2">
          <Sprout className="w-5 h-5 text-krishirin-primary-light" />
          Market Research & Advisory
        </h3>
        <pre className="text-xs text-krishirin-text-muted bg-gray-50 rounded-lg p-3 overflow-auto max-h-60 whitespace-pre-wrap">
          {JSON.stringify(advisory, null, 2)}
        </pre>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-krishirin-border bg-krishirin-surface p-5 space-y-4">
      <h3 className="font-semibold text-krishirin-text flex items-center gap-2">
        <Sprout className="w-5 h-5 text-krishirin-primary-light" />
        Agricultural Advisory Plan
      </h3>

      {landAssessment && (
        <div className="text-sm text-krishirin-text-muted bg-gray-50 rounded-lg p-3">
          {landAssessment}
        </div>
      )}

      {sowingPlan.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-krishirin-text mb-2 flex items-center gap-1">
            <Calendar className="w-4 h-4 text-krishirin-primary" />
            Sowing Plan
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-krishirin-border">
                  <th className="text-left py-2 px-2 font-medium text-krishirin-text-muted">Crop</th>
                  <th className="text-left py-2 px-2 font-medium text-krishirin-text-muted">Area</th>
                  <th className="text-left py-2 px-2 font-medium text-krishirin-text-muted">Season</th>
                  <th className="text-left py-2 px-2 font-medium text-krishirin-text-muted">Window</th>
                  <th className="text-right py-2 px-2 font-medium text-krishirin-text-muted">Revenue</th>
                </tr>
              </thead>
              <tbody>
                {sowingPlan.map((entry: Record<string, unknown>, i: number) => (
                  <tr key={i} className="border-b border-gray-100">
                    <td className="py-2 px-2 font-medium">{String(entry.crop ?? "")}</td>
                    <td className="py-2 px-2">{entry.area_acres ?? ""} ac</td>
                    <td className="py-2 px-2 capitalize">{String(entry.season ?? "")}</td>
                    <td className="py-2 px-2">{String(entry.sowing_window ?? "")}</td>
                    <td className="py-2 px-2 text-right font-medium text-krishirin-success">
                      ₹{Number(entry.expected_revenue ?? 0).toLocaleString("en-IN")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {inputCost && (
          <div className="bg-blue-50 rounded-lg p-3">
            <h4 className="text-xs font-medium text-blue-700 mb-1 flex items-center gap-1">
              <Coins className="w-3.5 h-3.5" /> Input Cost Guidance
            </h4>
            <p className="text-xs text-krishirin-text-muted">{inputCost}</p>
          </div>
        )}
        {weather && (
          <div className="bg-cyan-50 rounded-lg p-3">
            <h4 className="text-xs font-medium text-cyan-700 mb-1 flex items-center gap-1">
              <Cloud className="w-3.5 h-3.5" /> Weather Guidance
            </h4>
            <p className="text-xs text-krishirin-text-muted">{weather}</p>
          </div>
        )}
        {market && (
          <div className="bg-green-50 rounded-lg p-3">
            <h4 className="text-xs font-medium text-green-700 mb-1 flex items-center gap-1">
              <TrendingUp className="w-3.5 h-3.5" /> Market Timing
            </h4>
            <p className="text-xs text-krishirin-text-muted">{market}</p>
          </div>
        )}
        {diversification && (
          <div className="bg-purple-50 rounded-lg p-3">
            <h4 className="text-xs font-medium text-purple-700 mb-1 flex items-center gap-1">
              <Sprout className="w-3.5 h-3.5" /> Diversification
            </h4>
            <p className="text-xs text-krishirin-text-muted">{diversification}</p>
          </div>
        )}
      </div>
    </div>
  );
}
