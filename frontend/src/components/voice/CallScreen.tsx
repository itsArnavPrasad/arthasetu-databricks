"use client";

import {
  TranscriptOverlay,
  LED,
  Badge,
  usePipecatConnectionState,
} from "@pipecat-ai/voice-ui-kit";
import { PlasmaVisualizer } from "@pipecat-ai/voice-ui-kit/webgl";
import { CallControls } from "./CallControls";
import { CallStatus } from "./CallStatus";

interface CallScreenProps {
  handleConnect?: () => void | Promise<void>;
  handleDisconnect?: () => void | Promise<void>;
  error?: string | null;
  callType: "understanding" | "advisory";
  sidePanel?: React.ReactNode;
}

export function CallScreen({
  handleConnect,
  handleDisconnect,
  error,
  callType,
  sidePanel,
}: CallScreenProps) {
  const { isConnected, isConnecting } = usePipecatConnectionState();

  const title =
    callType === "understanding"
      ? "Understanding Call"
      : "Loan Advisory Call";

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 max-w-md text-center">
          <p className="text-red-700 font-medium mb-2">Connection Error</p>
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header bar */}
      <div className="flex items-center justify-between px-5 py-2.5 bg-white border-b border-krishirin-border shrink-0">
        <div className="flex items-center gap-3">
          <LED
            on={isConnected}
            blinking={isConnecting}
            blinkIntervalMs={500}
            className="size-2.5"
            classNames={{
              on: "bg-krishirin-success shadow-[0_0_8px_rgba(22,163,74,0.4)]",
              off: "bg-gray-300",
            }}
          />
          <h2 className="text-sm font-semibold text-krishirin-text tracking-tight">
            {title}
          </h2>
          <Badge
            color={callType === "understanding" ? "agent" : "warning"}
            variant="outline"
            size="sm"
          >
            {callType === "understanding" ? "Verification" : "Advisory"}
          </Badge>
        </div>
        <CallStatus />
      </div>

      {/* Main content: voice visualizer + side panel */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Voice visualizer */}
        <div
          className={`flex flex-col relative bg-gray-950 min-w-0 ${
            sidePanel ? "w-[40%]" : "flex-1"
          }`}
        >
          <div className="flex-1 relative overflow-hidden">
            <PlasmaVisualizer />

            {/* Floating transcript overlay with glass backdrop */}
            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 w-full max-w-lg px-4">
              <div className="transcript-overlay-glass rounded-xl px-5 py-3">
                <TranscriptOverlay
                  participant="remote"
                  className="text-white text-center text-lg drop-shadow-md"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right: Side panel */}
        {sidePanel && (
          <div className="w-[60%] border-l border-gray-200 bg-white flex flex-col shrink-0 overflow-hidden">
            {sidePanel}
          </div>
        )}
      </div>

      {/* Bottom: Call controls */}
      <CallControls
        handleConnect={handleConnect}
        handleDisconnect={handleDisconnect}
      />
    </div>
  );
}
