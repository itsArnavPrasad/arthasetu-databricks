"use client";

import { useState, useEffect, useCallback, useRef } from "react";

export interface AgentEvent {
  type: "agent_update" | "pipeline_complete" | "pipeline_error" | "heartbeat";
  agent?: string;
  title?: string;
  icon?: string;
  status?: "pending" | "processing" | "completed" | "failed";
  summary?: string;
  result?: Record<string, unknown>;
  error?: string;
  timestamp?: string;
}

export interface AgentCard {
  key: string;
  title: string;
  icon: string;
  status: "pending" | "processing" | "completed" | "failed";
  summary: string;
  result?: Record<string, unknown>;
}

export function useAgentEvents(sessionId: string | null) {
  const [cards, setCards] = useState<AgentCard[]>([]);
  const [pipelineComplete, setPipelineComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const connect = useCallback(() => {
    if (!sessionId) return;

    // Close existing connection
    eventSourceRef.current?.close();

    // SSE: use NEXT_PUBLIC_API_URL if set (cross-origin backend), otherwise
    // use relative URL which goes through the Next.js rewrite proxy.
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "";
    const es = new EventSource(`${backendUrl}/api/events/${sessionId}`);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const data: AgentEvent = JSON.parse(event.data);

        if (data.type === "agent_update" && data.agent) {
          setCards((prev) => {
            const existing = prev.findIndex((c) => c.key === data.agent);
            const card: AgentCard = {
              key: data.agent!,
              title: data.title || data.agent!,
              icon: data.icon || "⚙️",
              status: (data.status as AgentCard["status"]) || "completed",
              summary: data.summary || "",
              result: data.result,
            };

            if (existing >= 0) {
              const updated = [...prev];
              updated[existing] = card;
              return updated;
            }
            return [...prev, card];
          });
        } else if (data.type === "pipeline_complete") {
          setPipelineComplete(true);
        } else if (data.type === "pipeline_error") {
          setError(data.error || "Pipeline failed");
        }
      } catch {
        // Ignore parse errors
      }
    };

    es.onerror = () => {
      // SSE will auto-reconnect
    };
  }, [sessionId]);

  useEffect(() => {
    connect();
    return () => {
      eventSourceRef.current?.close();
    };
  }, [connect]);

  return { cards, pipelineComplete, error };
}
