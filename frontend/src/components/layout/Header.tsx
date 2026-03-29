"use client";

import { useApplication } from "@/context/ApplicationContext";
import { Sprout } from "lucide-react";

const phaseLabels: Record<string, string> = {
  apply: "Loan Application",
  analysis: "Document Analysis",
  call1: "Understanding Call",
  processing: "Strategy Planning",
  call2: "Advisory Call",
  summary: "Summary",
};

export function Header() {
  const { phase } = useApplication();

  return (
    <header className="h-14 border-b border-krishirin-border bg-krishirin-surface flex items-center justify-between px-4 shrink-0">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-krishirin-primary flex items-center justify-center">
          <Sprout className="w-5 h-5 text-white" />
        </div>
        <span className="font-bold text-lg text-krishirin-primary">
          KrishiRin
        </span>
        <span className="text-xs text-krishirin-text-muted ml-1">
          कृषिऋण
        </span>
      </div>
      <div className="text-sm font-medium text-krishirin-text-muted">
        {phaseLabels[phase] || ""}
      </div>
      <div className="text-xs text-krishirin-text-muted">
        Grameen Credit Advisory
      </div>
    </header>
  );
}
