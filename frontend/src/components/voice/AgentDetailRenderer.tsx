"use client";

import { useEffect, useState } from "react";
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis,
  Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const fmtTooltip = (v: any) => `₹${Number(v || 0).toLocaleString("en-IN")}`;

const COLORS = {
  green: "#16A34A", darkGreen: "#1B5E20", emerald: "#10B981",
  red: "#DC2626", amber: "#F59E0B", blue: "#2563EB",
  orange: "#FF6F00", purple: "#7C3AED",
};
const PIE_COLORS = [COLORS.green, COLORS.amber, COLORS.blue, COLORS.orange, COLORS.purple, COLORS.red];

interface Props { agentKey: string; result: Record<string, unknown>; }

export function AgentDetailRenderer({ agentKey, result }: Props) {
  switch (agentKey) {
    case "optimal_policy": return <LoanPolicyDetail data={result} />;
    case "agri_advisory": return <AgriAdvisoryDetail data={result} />;
    case "cashflow_map": return <CashflowDetail data={result} />;
    case "risk_plan": return <RiskPlanDetail data={result} />;
    case "call_insights": return <CallInsightsDetail data={result} />;
    case "scheme_matches": return <SchemeMatchDetail data={result} />;
    case "bank_products": return <BankComparisonDetail data={result} />;
    default: return <GenericDetail data={result} />;
  }
}

/* ── Helpers ─────────────────────────────────────────────── */
function str(v: unknown): string { return typeof v === "string" ? v : v == null ? "" : String(v); }
function num(v: unknown): number { return typeof v === "number" ? v : typeof v === "string" ? parseFloat(v) || 0 : 0; }
function arr(v: unknown): unknown[] { return Array.isArray(v) ? v : []; }
function fmt(n: number): string { return n >= 100000 ? `${(n / 100000).toFixed(1)}L` : n >= 1000 ? `${(n / 1000).toFixed(0)}K` : String(n); }

/* ── Shared Components ───────────────────────────────────── */

function Section({ title, accent = "emerald", children }: { title: string; accent?: string; children: React.ReactNode }) {
  const borderColor = accent === "amber" ? "border-l-amber-400" : accent === "red" ? "border-l-red-400" : accent === "blue" ? "border-l-blue-400" : "border-l-emerald-500";
  return (
    <div className={`mb-4 last:mb-0 pl-3 border-l-2 ${borderColor} animate-fade-in-up`}>
      <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">{title}</h4>
      {children}
    </div>
  );
}

function StatCard({ label, value, sub, icon, gradient }: { label: string; value: string; sub?: string; icon?: string; gradient?: string }) {
  const bg = gradient || "from-gray-50 to-white";
  return (
    <div className={`bg-gradient-to-br ${bg} rounded-xl p-3 border border-gray-100 shadow-sm`}>
      <div className="flex items-center gap-1.5">
        {icon && <span className="text-base">{icon}</span>}
        <span className="text-[10px] text-gray-500 font-medium">{label}</span>
      </div>
      <div className="text-sm font-bold text-gray-900 mt-1">{value}</div>
      {sub && <div className="text-[10px] text-gray-400 mt-0.5">{sub}</div>}
    </div>
  );
}

function Badge({ text, color = "gray" }: { text: string; color?: string }) {
  const c: Record<string, string> = {
    green: "bg-emerald-50 text-emerald-700 border-emerald-200",
    amber: "bg-amber-50 text-amber-700 border-amber-200",
    red: "bg-red-50 text-red-700 border-red-200",
    blue: "bg-blue-50 text-blue-700 border-blue-200",
    gray: "bg-gray-50 text-gray-500 border-gray-200",
  };
  return <span className={`text-[10px] px-2.5 py-1 rounded-full border font-semibold ${c[color] || c.gray}`}>{text}</span>;
}

function AnimatedNumber({ value, prefix = "", suffix = "" }: { value: number; prefix?: string; suffix?: string }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    if (value === 0) return;
    const duration = 800;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(Math.round(value * eased));
      if (t < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [value]);
  return <span>{prefix}{display.toLocaleString("en-IN")}{suffix}</span>;
}

/* ── Loan Policy ─────────────────────────────────────────── */

function LoanPolicyDetail({ data }: { data: Record<string, unknown> }) {
  const scheme = str(data.recommended_scheme) || "KCC";
  const bank = str(data.recommended_bank) || "SBI";
  const amount = num(data.final_amount);
  const rate = num(data.final_rate_effective || data.final_rate);
  const emi = num(data.monthly_emi_equivalent);
  const collateral = str(data.collateral_plan);
  const steps = arr(data.application_steps);
  const docs = arr(data.documents_needed);
  const days = num(data.estimated_processing_days);
  const rationale = str(data.rationale);
  const isWaived = collateral.toLowerCase().includes("waiv") || collateral.toLowerCase().includes("no collateral");

  const pieData = emi > 0 && amount > 0 ? [
    { name: "Monthly EMI", value: emi },
    { name: "Remaining Income", value: Math.max((amount / 12) - emi, emi * 0.5) },
  ] : [];

  return (
    <div className="space-y-4">
      {/* Hero Banner */}
      <div className="bg-gradient-to-r from-emerald-600 to-green-700 rounded-xl p-4 text-white shadow-lg">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[10px] uppercase tracking-widest opacity-80">Recommended</div>
            <div className="text-lg font-bold mt-0.5">{scheme}</div>
            <div className="text-xs opacity-90">via {bank}</div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-black"><AnimatedNumber value={amount} prefix="₹" /></div>
            <div className="text-xs opacity-80">{rate}% effective p.a.</div>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-3 gap-2">
        <StatCard label="Monthly EMI" value={`₹${fmt(emi)}`} icon="💰" gradient="from-emerald-50 to-white" />
        <StatCard label="Processing" value={`${days} days`} icon="⏱️" gradient="from-blue-50 to-white" />
        <StatCard label="Collateral" value={isWaived ? "Waived" : "Required"} icon={isWaived ? "✅" : "⚠️"} gradient={isWaived ? "from-green-50 to-white" : "from-amber-50 to-white"} />
      </div>

      {/* Rate Comparison */}
      <Section title="Interest Rate Breakdown">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-gray-500 w-16">Nominal</span>
            <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
              <div className="h-full bg-red-300 rounded-full" style={{ width: "70%" }} />
            </div>
            <span className="text-[10px] font-bold text-red-500 w-10 text-right">7%</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-gray-500 w-16">Effective</span>
            <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-emerald-400 to-emerald-500 rounded-full" style={{ width: `${(rate / 7) * 70}%` }} />
            </div>
            <span className="text-[10px] font-bold text-emerald-600 w-10 text-right">{rate}%</span>
          </div>
          <p className="text-[10px] text-gray-400">2% govt subvention + {7 - rate - 2}% prompt repayment incentive</p>
        </div>
      </Section>

      {/* EMI Pie */}
      {pieData.length > 0 && (
        <Section title="EMI Affordability">
          <div className="flex items-center gap-3">
            <ResponsiveContainer width={80} height={80}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={22} outerRadius={35} dataKey="value" strokeWidth={0}>
                  <Cell fill={COLORS.green} />
                  <Cell fill="#E5E7EB" />
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div>
              <div className="text-sm font-bold text-gray-900">₹{emi.toLocaleString("en-IN")}/mo</div>
              <div className="text-[10px] text-gray-400">Harvest-aligned repayment</div>
            </div>
          </div>
        </Section>
      )}

      {/* Application Steps */}
      {steps.length > 0 && (
        <Section title="How to Apply" accent="blue">
          <div className="space-y-0">
            {steps.map((s, i) => (
              <div key={i} className="flex gap-3 animate-fade-in-up" style={{ animationDelay: `${i * 100}ms` }}>
                <div className="flex flex-col items-center">
                  <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-[10px] font-bold shrink-0">{i + 1}</div>
                  {i < steps.length - 1 && <div className="w-0.5 h-full bg-emerald-100 my-0.5" />}
                </div>
                <div className="text-xs text-gray-700 pb-3">{str(s)}</div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Documents */}
      {docs.length > 0 && (
        <Section title="Documents Checklist">
          <div className="grid grid-cols-2 gap-1.5">
            {docs.map((d, i) => (
              <div key={i} className="flex items-center gap-2 text-xs text-gray-600 bg-gray-50 rounded-lg px-2.5 py-1.5">
                <div className="w-3.5 h-3.5 rounded border-2 border-gray-300 shrink-0" />
                {str(d)}
              </div>
            ))}
          </div>
        </Section>
      )}

      {rationale && <p className="text-[10px] text-gray-400 italic bg-gray-50 rounded-lg p-2.5">{rationale}</p>}
    </div>
  );
}

/* ── Agricultural Advisory ───────────────────────────────── */

function AgriAdvisoryDetail({ data }: { data: Record<string, unknown> }) {
  const assessment = str(data.land_assessment);
  const allocations = arr(data.allocations);
  const diversification = arr(data.income_diversification);
  const revenue = num(data.total_expected_revenue);
  const costTotal = num(data.total_expected_costs);
  const net = num(data.net_expected_income);
  const summary = str(data.advisory_summary);
  const selling = str(data.selling_strategy);

  const pieData = allocations.map((a, i) => {
    const alloc = a as Record<string, unknown>;
    return { name: str(alloc.crop), value: num(alloc.area_acres), color: PIE_COLORS[i % PIE_COLORS.length] };
  });

  const barData = allocations.map((a) => {
    const alloc = a as Record<string, unknown>;
    return { crop: str(alloc.crop).slice(0, 8), revenue: num(alloc.expected_revenue), yield: num(alloc.expected_yield_qtl) };
  });

  return (
    <div className="space-y-4">
      {assessment && <p className="text-xs text-gray-600 bg-emerald-50 border border-emerald-100 rounded-xl p-3">{assessment}</p>}

      {/* Financial Summary */}
      <div className="grid grid-cols-3 gap-2">
        <StatCard label="Revenue" value={`₹${fmt(revenue)}`} icon="📈" gradient="from-emerald-50 to-white" />
        <StatCard label="Costs" value={`₹${fmt(costTotal)}`} icon="📉" gradient="from-red-50 to-white" />
        <StatCard label="Net Income" value={`₹${fmt(net)}`} icon="💵" gradient="from-green-50 to-white" />
      </div>

      {/* Crop Allocation Pie */}
      {pieData.length > 0 && (
        <Section title="Crop Area Allocation">
          <div className="flex items-center gap-2">
            <ResponsiveContainer width={90} height={90}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" outerRadius={40} dataKey="value" strokeWidth={2} stroke="#fff">
                  {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Pie>
                <Tooltip formatter={(v: unknown) => `${v} acres`} />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex-1 space-y-1">
              {pieData.map((p, i) => (
                <div key={i} className="flex items-center gap-2 text-xs">
                  <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: p.color }} />
                  <span className="text-gray-700 font-medium">{p.name}</span>
                  <span className="text-gray-400 ml-auto">{p.value} ac</span>
                </div>
              ))}
            </div>
          </div>
        </Section>
      )}

      {/* Revenue Bar Chart */}
      {barData.length > 0 && (
        <Section title="Expected Revenue by Crop">
          <ResponsiveContainer width="100%" height={100}>
            <BarChart data={barData} barSize={20}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="crop" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 9 }} tickFormatter={(v) => `₹${fmt(v)}`} width={45} />
              <Tooltip formatter={fmtTooltip} />
              <Bar dataKey="revenue" radius={[4, 4, 0, 0]}>
                {barData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Section>
      )}

      {/* Crop Details Table */}
      {allocations.length > 0 && (
        <Section title="Sowing Plan">
          <div className="rounded-lg overflow-hidden border border-gray-100">
            <table className="w-full text-[10px]">
              <thead><tr className="bg-gray-50 text-gray-500">
                <th className="px-2 py-1.5 text-left font-semibold">Crop</th>
                <th className="px-2 py-1.5 text-right font-semibold">Area</th>
                <th className="px-2 py-1.5 text-right font-semibold">Revenue</th>
                <th className="px-2 py-1.5 text-left font-semibold">Sow</th>
              </tr></thead>
              <tbody>{allocations.map((a, i) => {
                const alloc = a as Record<string, unknown>;
                return (
                  <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-gray-50/50"}>
                    <td className="px-2 py-1.5 font-medium text-gray-800">{str(alloc.crop)}</td>
                    <td className="px-2 py-1.5 text-right text-gray-600">{num(alloc.area_acres)} ac</td>
                    <td className="px-2 py-1.5 text-right text-emerald-600 font-semibold">₹{fmt(num(alloc.expected_revenue))}</td>
                    <td className="px-2 py-1.5 text-gray-500">{str(alloc.sowing_window)}</td>
                  </tr>
                );
              })}</tbody>
            </table>
          </div>
        </Section>
      )}

      {selling && (
        <Section title="Selling Strategy" accent="amber">
          <p className="text-xs text-gray-700">{selling}</p>
        </Section>
      )}

      {diversification.length > 0 && (
        <Section title="Income Diversification">
          <div className="grid grid-cols-1 gap-1.5">
            {diversification.map((d, i) => (
              <div key={i} className="flex items-center gap-2 bg-amber-50 border border-amber-100 rounded-lg px-3 py-2 text-xs text-amber-800">
                <span>💡</span>{str(d)}
              </div>
            ))}
          </div>
        </Section>
      )}

      {summary && (
        <div className="bg-gradient-to-r from-emerald-50 to-green-50 border border-emerald-200 rounded-xl p-3">
          <p className="text-xs text-emerald-800 font-medium leading-relaxed">{summary}</p>
        </div>
      )}
    </div>
  );
}

/* ── Cashflow Map ────────────────────────────────────────── */

function CashflowDetail({ data }: { data: Record<string, unknown> }) {
  const projections = arr(data.monthly_projections);
  const surplusMonths = arr(data.surplus_months);
  const deficitMonths = arr(data.deficit_months);
  const buffer = num(data.buffer_needed);
  const bufferStrategy = str(data.buffer_strategy);
  const annualSummary = str(data.annual_summary);

  const chartData = projections.slice(0, 12).map((m) => {
    const month = m as Record<string, unknown>;
    const income = num(month.total_income);
    const emi = num(month.loan_emi);
    return { month: str(month.month).slice(0, 3), income, emi, surplus: income - emi };
  });

  return (
    <div className="space-y-4">
      {/* Bar Chart */}
      {chartData.length > 0 && (
        <Section title="12-Month Income vs EMI">
          <ResponsiveContainer width="100%" height={130}>
            <BarChart data={chartData} barGap={1}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" tick={{ fontSize: 9 }} />
              <YAxis tick={{ fontSize: 9 }} tickFormatter={(v) => `₹${fmt(v)}`} width={42} />
              <Tooltip formatter={fmtTooltip} />
              <Bar dataKey="income" name="Income" fill={COLORS.green} radius={[3, 3, 0, 0]} barSize={12} />
              <Bar dataKey="emi" name="EMI" fill={COLORS.red} radius={[3, 3, 0, 0]} barSize={12} />
            </BarChart>
          </ResponsiveContainer>
        </Section>
      )}

      {/* Surplus/Deficit Badges */}
      <div className="flex gap-2 flex-wrap">
        {surplusMonths.map((m, i) => <Badge key={`s${i}`} text={`${str(m)} ↑`} color="green" />)}
        {deficitMonths.map((m, i) => <Badge key={`d${i}`} text={`${str(m)} ↓`} color="red" />)}
      </div>

      {/* Buffer Strategy */}
      {buffer > 0 && (
        <Section title="Emergency Buffer" accent="amber">
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-amber-800 font-semibold">Target: ₹{buffer.toLocaleString("en-IN")}</span>
              <span className="text-[10px] text-amber-600">3 months EMI</span>
            </div>
            <div className="h-2 bg-amber-100 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-amber-400 to-amber-500 rounded-full w-0 transition-all duration-1000" style={{ width: "0%" }} />
            </div>
            {bufferStrategy && <p className="text-[10px] text-amber-700 mt-2">{bufferStrategy}</p>}
          </div>
        </Section>
      )}

      {annualSummary && <p className="text-xs text-blue-700 bg-blue-50 border border-blue-100 rounded-xl p-3 font-medium">{annualSummary}</p>}
    </div>
  );
}

/* ── Risk Plan ───────────────────────────────────────────── */

function RiskPlanDetail({ data }: { data: Record<string, unknown> }) {
  const actions = arr(data.actions);
  const insurance = str(data.insurance_plan);
  const buffer = str(data.savings_buffer_target);
  const docs = arr(data.documentation_checklist);
  const level = str(data.overall_risk_level).toLowerCase();

  const gaugeAngle = level === "low" ? 30 : level === "moderate" ? 90 : level === "elevated" || level === "high" ? 140 : 90;
  const gaugeColor = level === "low" ? COLORS.green : level === "moderate" ? COLORS.amber : COLORS.red;

  return (
    <div className="space-y-4">
      {/* Risk Gauge */}
      <div className="flex flex-col items-center py-2">
        <div className="relative w-28 h-16 overflow-hidden">
          <div className="absolute inset-0 border-[6px] border-gray-200 rounded-t-full" />
          <div className="absolute inset-0 border-[6px] border-transparent rounded-t-full"
            style={{ borderTopColor: gaugeColor, borderLeftColor: gaugeAngle > 90 ? gaugeColor : "transparent", borderRightColor: gaugeAngle < 90 ? gaugeColor : "transparent", transform: `rotate(${gaugeAngle - 90}deg)`, transformOrigin: "bottom center" }} />
          <div className="absolute bottom-0 left-1/2 w-1 h-10 -translate-x-1/2 origin-bottom transition-transform duration-1000" style={{ transform: `translateX(-50%) rotate(${gaugeAngle - 90}deg)`, background: gaugeColor }} />
        </div>
        <Badge text={level || "assessed"} color={level === "low" ? "green" : level === "moderate" ? "amber" : "red"} />
      </div>

      {/* Mitigation Actions */}
      {actions.length > 0 && (
        <Section title="Action Plan">
          <div className="space-y-2">
            {actions.map((a, i) => {
              const action = a as Record<string, unknown>;
              const priority = str(action.priority).toLowerCase();
              const borderColor = priority === "high" ? "border-l-red-500" : priority === "medium" ? "border-l-amber-400" : "border-l-emerald-400";
              const bg = priority === "high" ? "bg-red-50" : priority === "medium" ? "bg-amber-50" : "bg-emerald-50";
              return (
                <div key={i} className={`${bg} border-l-3 ${borderColor} rounded-r-lg p-2.5 animate-fade-in-up`} style={{ animationDelay: `${i * 80}ms`, borderLeftWidth: "3px" }}>
                  <div className="flex items-start justify-between gap-2">
                    <div className="text-xs text-gray-800 font-medium">{str(action.mitigation)}</div>
                    <Badge text={priority} color={priority === "high" ? "red" : priority === "medium" ? "amber" : "green"} />
                  </div>
                  <div className="text-[10px] text-gray-500 mt-0.5">{str(action.risk)}</div>
                </div>
              );
            })}
          </div>
        </Section>
      )}

      {insurance && (
        <Section title="Insurance" accent="blue">
          <div className="bg-blue-50 border border-blue-100 rounded-lg p-2.5">
            <p className="text-xs text-blue-800">{insurance}</p>
          </div>
        </Section>
      )}

      {buffer && (
        <Section title="Savings Buffer" accent="amber">
          <p className="text-xs text-gray-700 font-medium">{buffer}</p>
        </Section>
      )}

      {docs.length > 0 && (
        <Section title="Documentation Checklist">
          <div className="space-y-1">
            {docs.map((d, i) => (
              <div key={i} className="flex items-center gap-2 text-xs text-gray-600">
                <div className="w-3.5 h-3.5 rounded border-2 border-gray-300 shrink-0" />
                {str(d)}
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

/* ── Call Insights ────────────────────────────────────────── */

function CallInsightsDetail({ data }: { data: Record<string, unknown> }) {
  const status = str(data.acceptance_status);
  const requirement = str(data.stated_requirement);
  const concerns = arr(data.concerns);
  const crops = arr(data.crop_preferences);
  const summary = str(data.call_summary);

  const statusColor = status === "accepted" ? "green" : status === "rejected" ? "red" : "amber";
  const statusBg = status === "accepted" ? "from-emerald-50 to-green-50" : status === "rejected" ? "from-red-50 to-rose-50" : "from-amber-50 to-yellow-50";

  return (
    <div className="space-y-3">
      <div className={`bg-gradient-to-r ${statusBg} rounded-xl p-3 flex items-center justify-between`}>
        <div>
          <div className="text-[10px] text-gray-500 uppercase tracking-wider">Farmer Status</div>
          <div className="text-sm font-bold text-gray-900 mt-0.5 capitalize">{status || "Analyzed"}</div>
        </div>
        <Badge text={status || "analyzed"} color={statusColor} />
      </div>

      {requirement && (
        <div className="bg-gray-50 border-l-3 border-l-blue-400 rounded-r-lg p-3" style={{ borderLeftWidth: "3px" }}>
          <div className="text-[10px] text-gray-400 mb-1">Stated Requirement</div>
          <p className="text-xs text-gray-800 font-medium">{requirement}</p>
        </div>
      )}

      {concerns.length > 0 && (
        <Section title="Concerns" accent="amber">
          <div className="flex flex-wrap gap-1.5">
            {concerns.map((c, i) => <Badge key={i} text={str(c)} color="amber" />)}
          </div>
        </Section>
      )}

      {crops.length > 0 && (
        <Section title="Preferred Crops">
          <div className="flex flex-wrap gap-1.5">
            {crops.map((c, i) => <Badge key={i} text={str(c)} color="green" />)}
          </div>
        </Section>
      )}

      {summary && <p className="text-xs text-gray-500 italic">{summary}</p>}
    </div>
  );
}

/* ── Scheme Matching ─────────────────────────────────────── */

function SchemeMatchDetail({ data }: { data: Record<string, unknown> }) {
  const matches = arr(data.matches || data.eligible_schemes);
  const best = str(data.best_scheme || data.recommended_primary);
  const rationale = str(data.rationale || data.key_findings);

  return (
    <div className="space-y-3">
      {matches.length > 0 ? (
        <div className="space-y-2">
          {matches.map((m, i) => {
            const scheme = m as Record<string, unknown>;
            const name = str(scheme.name || scheme.scheme_name);
            const eligible = scheme.eligibility_met !== false && scheme.eligible !== false;
            const isBest = name.toLowerCase().includes(best.toLowerCase());
            return (
              <div key={i} className={`rounded-lg border p-2.5 ${isBest ? "border-emerald-300 bg-emerald-50 shadow-sm" : "border-gray-100 bg-white"}`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-gray-900">{name}</span>
                  <Badge text={eligible ? "Eligible" : "Not Eligible"} color={eligible ? "green" : "red"} />
                </div>
                {(str(scheme.interest_rate) || str(scheme.max_amount)) && (
                  <div className="flex gap-3 mt-1.5 text-[10px] text-gray-500">
                    {str(scheme.interest_rate) && <span>Rate: {str(scheme.interest_rate)}</span>}
                    {str(scheme.max_amount) && <span>Max: {str(scheme.max_amount)}</span>}
                    {str(scheme.processing_time_days) && <span>{str(scheme.processing_time_days)}d</span>}
                  </div>
                )}
                {isBest && <div className="text-[10px] text-emerald-600 font-semibold mt-1">Best Match</div>}
              </div>
            );
          })}
        </div>
      ) : (
        <GenericDetail data={data} />
      )}
      {rationale && <p className="text-[10px] text-gray-400 italic">{rationale}</p>}
    </div>
  );
}

/* ── Bank Comparison ─────────────────────────────────────── */

function BankComparisonDetail({ data }: { data: Record<string, unknown> }) {
  const products = arr(data.products);
  const summary = str(data.comparison_summary);

  return (
    <div className="space-y-3">
      {products.length > 0 ? (
        <div className="rounded-lg overflow-hidden border border-gray-100">
          <table className="w-full text-[10px]">
            <thead><tr className="bg-gray-50 text-gray-500">
              <th className="px-2 py-1.5 text-left font-semibold">Bank</th>
              <th className="px-2 py-1.5 text-right font-semibold">Rate</th>
              <th className="px-2 py-1.5 text-right font-semibold">Fee</th>
              <th className="px-2 py-1.5 text-right font-semibold">Days</th>
            </tr></thead>
            <tbody>{products.map((p, i) => {
              const bank = p as Record<string, unknown>;
              return (
                <tr key={i} className={i === 0 ? "bg-emerald-50" : i % 2 === 0 ? "bg-white" : "bg-gray-50/50"}>
                  <td className="px-2 py-1.5 font-medium text-gray-800">{str(bank.bank_name)}</td>
                  <td className="px-2 py-1.5 text-right text-gray-600">{str(bank.interest_rate)}</td>
                  <td className="px-2 py-1.5 text-right text-gray-600">{str(bank.processing_fee)}</td>
                  <td className="px-2 py-1.5 text-right text-gray-600">{str(bank.processing_time_days)}</td>
                </tr>
              );
            })}</tbody>
          </table>
        </div>
      ) : (
        <GenericDetail data={data} />
      )}
      {summary && <p className="text-xs text-gray-500 italic mt-2">{summary}</p>}
    </div>
  );
}

/* ── Generic Fallback ────────────────────────────────────── */

function GenericDetail({ data }: { data: Record<string, unknown> }) {
  const entries = Object.entries(data).filter(([, v]) => v != null && v !== "");
  if (entries.length === 0) return <p className="text-xs text-gray-400">No data available</p>;

  return (
    <div className="space-y-1.5">
      {entries.slice(0, 15).map(([key, val]) => (
        <div key={key} className="flex gap-2 text-xs">
          <span className="text-blue-500 font-mono shrink-0">{key}:</span>
          <span className="text-gray-700 break-words">
            {typeof val === "object" ? JSON.stringify(val, null, 1).slice(0, 200) : String(val ?? "").slice(0, 200)}
          </span>
        </div>
      ))}
    </div>
  );
}
