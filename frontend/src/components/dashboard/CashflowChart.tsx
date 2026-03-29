"use client";

import type { CashflowEntry } from "@/lib/types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";

interface CashflowChartProps {
  cashflow: CashflowEntry[];
}

export default function CashflowChart({ cashflow }: CashflowChartProps) {
  const data = cashflow.map((entry) => ({
    month: entry.month.slice(0, 3),
    income: entry.total_income,
    emi: entry.emi_due,
    surplus: entry.surplus,
  }));

  const formatRupee = (value: number) => {
    if (value >= 1000) return `₹${(value / 1000).toFixed(0)}K`;
    return `₹${value}`;
  };

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
          barCategoryGap="20%"
        >
          <XAxis
            dataKey="month"
            tick={{ fontSize: 11, fill: "#6B7280" }}
            axisLine={{ stroke: "#E5E7EB" }}
            tickLine={false}
          />
          <YAxis
            tickFormatter={formatRupee}
            tick={{ fontSize: 10, fill: "#6B7280" }}
            axisLine={false}
            tickLine={false}
            width={48}
          />
          <Tooltip
            formatter={(value, name) => [
              `₹${Number(value).toLocaleString("en-IN")}`,
              name === "income" ? "Income" : name === "emi" ? "EMI Due" : "Surplus",
            ]}
            contentStyle={{
              fontSize: 12,
              borderRadius: 8,
              border: "1px solid #E5E7EB",
              boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
            }}
          />
          <ReferenceLine y={0} stroke="#E5E7EB" />
          <Bar dataKey="income" radius={[4, 4, 0, 0]} maxBarSize={24}>
            {data.map((_, i) => (
              <Cell key={i} fill="#16A34A" fillOpacity={0.8} />
            ))}
          </Bar>
          <Bar dataKey="emi" radius={[4, 4, 0, 0]} maxBarSize={24}>
            {data.map((_, i) => (
              <Cell key={i} fill="#DC2626" fillOpacity={0.6} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
