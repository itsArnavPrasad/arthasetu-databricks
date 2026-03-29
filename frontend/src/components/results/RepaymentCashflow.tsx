"use client";

import type { CashflowEntry } from "@/lib/types";
import { Wallet } from "lucide-react";

interface RepaymentCashflowProps {
  cashflow: CashflowEntry[];
}

export function RepaymentCashflow({ cashflow }: RepaymentCashflowProps) {
  return (
    <div className="rounded-xl border border-krishirin-border bg-krishirin-surface p-5">
      <h3 className="font-semibold text-krishirin-text mb-4 flex items-center gap-2">
        <Wallet className="w-5 h-5 text-krishirin-secondary" />
        Month-by-Month Repayment Cashflow
      </h3>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b-2 border-krishirin-border">
              <th className="text-left py-2 px-2 font-medium text-krishirin-text-muted">Month</th>
              <th className="text-right py-2 px-2 font-medium text-krishirin-text-muted">Income</th>
              <th className="text-right py-2 px-2 font-medium text-krishirin-text-muted">EMI Due</th>
              <th className="text-right py-2 px-2 font-medium text-krishirin-text-muted">Surplus</th>
              <th className="text-left py-2 px-2 font-medium text-krishirin-text-muted">Sources</th>
            </tr>
          </thead>
          <tbody>
            {cashflow.map((entry, i) => (
              <tr
                key={i}
                className={`border-b border-gray-100 ${
                  entry.surplus < 0 ? "bg-red-50" : ""
                }`}
              >
                <td className="py-2 px-2 font-medium">{entry.month}</td>
                <td className="py-2 px-2 text-right text-krishirin-success font-medium">
                  ₹{entry.total_income.toLocaleString("en-IN")}
                </td>
                <td className="py-2 px-2 text-right text-krishirin-danger font-medium">
                  ₹{entry.emi_due.toLocaleString("en-IN")}
                </td>
                <td
                  className={`py-2 px-2 text-right font-bold ${
                    entry.surplus >= 0
                      ? "text-krishirin-success"
                      : "text-krishirin-danger"
                  }`}
                >
                  {entry.surplus >= 0 ? "+" : ""}₹
                  {entry.surplus.toLocaleString("en-IN")}
                </td>
                <td className="py-2 px-2 text-krishirin-text-muted">
                  {entry.income_sources.map((s) => s.source).join(", ")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
