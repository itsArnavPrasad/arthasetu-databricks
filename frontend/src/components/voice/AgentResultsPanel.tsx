"use client";

import { useAgentEvents } from "@/hooks/useAgentEvents";
import { AgentResultCard } from "./AgentResultCard";

interface AgentResultsPanelProps {
  sessionId: string | null;
}

export function AgentResultsPanel({ sessionId }: AgentResultsPanelProps) {
  const { cards, pipelineComplete, error } = useAgentEvents(sessionId);

  if (!sessionId) {
    return (
      <div className="h-full flex items-center justify-center p-6">
        <div className="text-center">
          <div className="text-4xl mb-3">🔍</div>
          <p className="text-gray-400 text-sm">
            Agent analysis will appear here once the call begins
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 bg-white">
        <h2 className="text-sm font-semibold text-gray-900">
          Live Analysis
        </h2>
        <p className="text-xs text-gray-500 mt-0.5">
          {pipelineComplete
            ? "All analysis complete"
            : cards.length === 0
            ? "Waiting for analysis trigger..."
            : `${cards.filter((c) => c.status === "completed").length}/${cards.length} agents finished`}
        </p>
      </div>

      {/* Cards list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {cards.map((card, i) => (
          <AgentResultCard key={card.key} card={card} index={i} />
        ))}

        {cards.length === 0 && sessionId && (
          <div className="flex flex-col items-center justify-center py-12">
            <div className="text-4xl mb-3">🔍</div>
            <p className="text-sm text-gray-400 text-center">
              The voice agent will trigger analysis
              <br />
              after clarification questions are answered
            </p>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="px-4 py-2 bg-red-50 border-t border-red-200">
          <p className="text-xs text-red-600">{error}</p>
        </div>
      )}

      {/* Completion banner */}
      {pipelineComplete && (
        <div className="px-4 py-3 bg-emerald-50 border-t border-emerald-200">
          <p className="text-xs text-emerald-700 font-medium">
            All agents complete — results presented to farmer
          </p>
        </div>
      )}
    </div>
  );
}
