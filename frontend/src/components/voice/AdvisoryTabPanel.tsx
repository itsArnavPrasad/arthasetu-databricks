"use client";

import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "@pipecat-ai/voice-ui-kit";
import { BarChart3, MessageSquare } from "lucide-react";
import { AgentResultsPanel } from "./AgentResultsPanel";
import { LiveTranscript } from "./LiveTranscript";

interface AdvisoryTabPanelProps {
  sessionId: string | null;
}

export function AdvisoryTabPanel({ sessionId }: AdvisoryTabPanelProps) {
  return (
    <Tabs
      defaultValue="analysis"
      className="advisory-tabs flex flex-col h-full"
    >
      {/* Tab bar */}
      <div className="px-3 pt-3 pb-0 bg-white border-b border-krishirin-border">
        <TabsList className="w-full">
          <TabsTrigger value="analysis" className="flex-1">
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Live Analysis</span>
          </TabsTrigger>
          <TabsTrigger value="transcript" className="flex-1">
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Transcript</span>
          </TabsTrigger>
        </TabsList>
      </div>

      {/* Analysis tab */}
      <TabsContent value="analysis" className="flex-1 overflow-hidden">
        <AgentResultsPanel sessionId={sessionId} />
      </TabsContent>

      {/* Transcript tab */}
      <TabsContent value="transcript" className="flex-1 overflow-hidden">
        <LiveTranscript
          assistantLabel="KrishiRin AI"
          clientLabel="Farmer"
        />
      </TabsContent>
    </Tabs>
  );
}
