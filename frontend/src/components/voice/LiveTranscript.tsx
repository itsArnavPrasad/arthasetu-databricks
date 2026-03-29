"use client";

import {
  Conversation,
  LED,
  Badge,
  usePipecatConnectionState,
  usePipecatConversation,
} from "@pipecat-ai/voice-ui-kit";
import { MessageSquare } from "lucide-react";

interface LiveTranscriptProps {
  assistantLabel?: string;
  clientLabel?: string;
}

export function LiveTranscript({
  assistantLabel = "KrishiRin AI",
  clientLabel = "Farmer",
}: LiveTranscriptProps) {
  const { isConnected, isConnecting } = usePipecatConnectionState();
  const { messages } = usePipecatConversation();

  const messageCount = messages.length;

  return (
    <div className="krishirin-transcript flex flex-col h-full bg-white">
      {/* Header */}
      <div className="px-4 py-3 border-b border-krishirin-border bg-gradient-to-r from-white to-green-50/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <LED
              on={isConnected}
              blinking={isConnecting}
              blinkIntervalMs={400}
              className="size-2.5"
              classNames={{
                on: "bg-krishirin-success shadow-[0_0_6px_rgba(22,163,74,0.5)]",
                off: "bg-krishirin-border",
              }}
            />
            <div className="flex items-center gap-2">
              <MessageSquare className="w-3.5 h-3.5 text-krishirin-primary" />
              <h3 className="text-sm font-semibold text-krishirin-text tracking-tight">
                Live Transcript
              </h3>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isConnected && (
              <Badge color="active" variant="outline" size="sm">
                LIVE
              </Badge>
            )}
            {messageCount > 0 && (
              <span className="text-[10px] font-mono text-krishirin-text-muted bg-gray-100 px-1.5 py-0.5 rounded">
                {messageCount} msg{messageCount !== 1 ? "s" : ""}
              </span>
            )}
          </div>
        </div>
        {isConnecting && (
          <p className="text-[11px] text-krishirin-warning mt-1.5 flex items-center gap-1">
            <span className="inline-block w-1 h-1 rounded-full bg-krishirin-warning animate-pulse" />
            Connecting to voice channel...
          </p>
        )}
        {isConnected && messageCount === 0 && (
          <p className="text-[11px] text-krishirin-text-muted mt-1.5">
            Listening — transcript will appear as you speak...
          </p>
        )}
      </div>

      {/* Conversation area */}
      <div className="flex-1 overflow-hidden bg-krishirin-bg">
        <Conversation
          assistantLabel={assistantLabel}
          clientLabel={clientLabel}
          noTextInput
          noFunctionCalls
          classNames={{
            container: "h-full transcript-scroll px-3 py-2",
            message: "mb-1",
          }}
        />
      </div>

      {/* Footer status bar */}
      <div className="px-4 py-2 border-t border-krishirin-border bg-white">
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-krishirin-text-muted">
            {isConnected
              ? "Voice active — Hindi & English"
              : "Awaiting connection"}
          </span>
          <div className="flex items-center gap-1">
            <span
              className={`inline-block w-1.5 h-1.5 rounded-full ${
                isConnected
                  ? "bg-krishirin-success animate-pulse"
                  : "bg-gray-300"
              }`}
            />
            <span className="text-[10px] text-krishirin-text-muted font-medium">
              {isConnected ? "Active" : "Idle"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
