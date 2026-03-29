"use client";

import {
  ConnectButton,
  UserAudioControl,
  ControlBar,
  ControlBarDivider,
} from "@pipecat-ai/voice-ui-kit";
import { PhoneOff, Phone } from "lucide-react";

interface CallControlsProps {
  handleConnect?: () => void | Promise<void>;
  handleDisconnect?: () => void | Promise<void>;
}

export function CallControls({
  handleConnect,
  handleDisconnect,
}: CallControlsProps) {
  return (
    <div className="flex items-center justify-center p-3 bg-gray-950 shrink-0">
      <ControlBar
        noAnimateIn
        className="bg-gray-900 border-gray-700 rounded-2xl"
      >
        <UserAudioControl size="lg" />
        <ControlBarDivider className="bg-gray-700" />
        <ConnectButton
          size="lg"
          onConnect={handleConnect}
          onDisconnect={handleDisconnect}
          stateContent={{
            disconnected: {
              children: (
                <span className="flex items-center gap-2">
                  <Phone className="w-4 h-4" />
                  <span>Call Shuru Karein</span>
                </span>
              ),
              variant: "primary",
            },
            connecting: {
              children: (
                <span className="flex items-center gap-2">
                  <span>Connecting...</span>
                </span>
              ),
              variant: "secondary",
            },
            connected: {
              children: (
                <span className="flex items-center gap-2">
                  <PhoneOff className="w-4 h-4" />
                  <span>Call Khatam Karein</span>
                </span>
              ),
              variant: "destructive",
            },
          }}
        />
      </ControlBar>
    </div>
  );
}
