"use client";

import { useEffect, useState } from "react";

interface ScoreGaugeProps {
  score: number;
  riskCategory: "A" | "B" | "C" | "D";
  size?: number;
}

const riskConfig = {
  A: { label: "Low Risk", color: "#16A34A", bg: "bg-green-50", trackColor: "#bbf7d0" },
  B: { label: "Moderate", color: "#F59E0B", bg: "bg-amber-50", trackColor: "#fde68a" },
  C: { label: "Elevated", color: "#EA580C", bg: "bg-orange-50", trackColor: "#fed7aa" },
  D: { label: "High Risk", color: "#DC2626", bg: "bg-red-50", trackColor: "#fecaca" },
};

export default function ScoreGauge({ score, riskCategory, size = 140 }: ScoreGaugeProps) {
  const [mounted, setMounted] = useState(false);
  const config = riskConfig[riskCategory];

  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;
  const offset = circumference - progress;

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 100);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="-rotate-90"
        >
          {/* Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={config.trackColor}
            strokeWidth={strokeWidth}
          />
          {/* Progress */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={config.color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={mounted ? offset : circumference}
            className="gauge-ring"
          />
        </svg>
        {/* Score text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="text-3xl font-bold leading-none"
            style={{ color: config.color }}
          >
            {score}
          </span>
          <span className="text-xs text-krishirin-text-muted mt-0.5">/100</span>
        </div>
      </div>
      {/* Badge */}
      <div
        className="mt-2 px-3 py-1 rounded-full text-xs font-semibold"
        style={{
          backgroundColor: `${config.color}15`,
          color: config.color,
        }}
      >
        {riskCategory} — {config.label}
      </div>
    </div>
  );
}
