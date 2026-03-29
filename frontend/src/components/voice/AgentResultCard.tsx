"use client";

import { useState, useEffect, useRef } from "react";
import type { AgentCard } from "@/hooks/useAgentEvents";
import { AgentDetailRenderer } from "./AgentDetailRenderer";

interface AgentResultCardProps {
  card: AgentCard;
  index?: number;
  defaultExpanded?: boolean;
}

export function AgentResultCard({ card, index = 0, defaultExpanded = false }: AgentResultCardProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const [justCompleted, setJustCompleted] = useState(false);
  const prevStatus = useRef(card.status);

  // Auto-expand on completion + green pulse
  useEffect(() => {
    if (prevStatus.current !== "completed" && card.status === "completed") {
      setJustCompleted(true);
      setExpanded(true);
      const timer = setTimeout(() => setJustCompleted(false), 1200);
      return () => clearTimeout(timer);
    }
    prevStatus.current = card.status;
  }, [card.status]);

  return (
    <div
      className={`
        rounded-xl border overflow-hidden transition-all duration-500
        animate-slide-up
        ${justCompleted ? "animate-pulse-green" : ""}
        ${card.status === "pending"
          ? "border-gray-200 bg-gray-50/70 opacity-60"
          : card.status === "processing"
          ? "border-amber-300 bg-amber-50/80 shadow-md shadow-amber-100/50"
          : card.status === "completed"
          ? "border-emerald-200 bg-white shadow-lg shadow-emerald-50/50"
          : "border-red-200 bg-red-50"
        }
      `}
      style={{ animationDelay: `${index * 80}ms` }}
    >
      {/* Header */}
      <button
        onClick={() => card.status === "completed" && card.result && setExpanded(!expanded)}
        className="w-full p-3.5 flex items-center gap-3 text-left hover:bg-gray-50/50 transition-colors"
        disabled={card.status !== "completed" || !card.result}
      >
        <div className="relative shrink-0">
          <span className="text-xl">{card.icon}</span>
          {card.status === "processing" && (
            <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse" />
          )}
          {card.status === "completed" && (
            <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-500" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <h3 className="text-xs font-bold text-gray-900 truncate">{card.title}</h3>
          {card.status === "processing" ? (
            <div className="mt-1.5 h-1.5 w-24 rounded-full shimmer-bg" />
          ) : (
            <p className={`text-[10px] truncate mt-0.5 ${
              card.status === "completed" ? "text-gray-500" : "text-gray-400"
            }`}>
              {card.summary}
            </p>
          )}
        </div>

        {card.status === "completed" && card.result && (
          <svg
            className={`w-3.5 h-3.5 text-gray-400 transition-transform duration-300 ${expanded ? "rotate-90" : ""}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        )}
      </button>

      {/* Expanded detail with smooth animation */}
      {expanded && card.result && (
        <div className="px-3.5 pb-3.5 border-t border-gray-100 pt-3 animate-expand-in">
          <AgentDetailRenderer agentKey={card.key} result={card.result} />
        </div>
      )}
    </div>
  );
}
