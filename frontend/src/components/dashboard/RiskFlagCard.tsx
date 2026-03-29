"use client";

import type { RiskFlag } from "@/lib/types";
import { AlertTriangle, AlertCircle, Info } from "lucide-react";

interface RiskFlagCardProps {
  flag: RiskFlag;
}

const flagConfig = {
  critical: {
    icon: AlertTriangle,
    bg: "bg-red-50",
    border: "border-red-200",
    iconColor: "text-red-600",
    badgeBg: "bg-red-100 text-red-700",
  },
  warning: {
    icon: AlertCircle,
    bg: "bg-amber-50",
    border: "border-amber-200",
    iconColor: "text-amber-600",
    badgeBg: "bg-amber-100 text-amber-700",
  },
  info: {
    icon: Info,
    bg: "bg-blue-50",
    border: "border-blue-200",
    iconColor: "text-blue-600",
    badgeBg: "bg-blue-100 text-blue-700",
  },
};

export default function RiskFlagCard({ flag }: RiskFlagCardProps) {
  const config = flagConfig[flag.type];
  const IconComponent = config.icon;

  return (
    <div
      className={`rounded-xl border ${config.border} ${config.bg} p-4 flex items-start gap-3 animate-fade-in-up`}
    >
      <div className={`shrink-0 mt-0.5 ${config.iconColor}`}>
        <IconComponent className="w-5 h-5" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${config.badgeBg}`}>
            {flag.category}
          </span>
        </div>
        <p className="text-sm text-krishirin-text leading-snug">
          {flag.description}
        </p>
        {flag.detail && (
          <p className="text-xs text-krishirin-text-muted mt-1">{flag.detail}</p>
        )}
      </div>
    </div>
  );
}
