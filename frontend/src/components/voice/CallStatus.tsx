"use client";

import { useState, useEffect, useRef } from "react";
import { usePipecatConnectionState } from "@pipecat-ai/voice-ui-kit";
import { Phone, PhoneOff, Loader2 } from "lucide-react";

export function CallStatus() {
  const { isConnected, isConnecting } = usePipecatConnectionState();
  const [duration, setDuration] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (isConnected) {
      setDuration(0);
      intervalRef.current = setInterval(() => {
        setDuration((d) => d + 1);
      }, 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isConnected]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60)
      .toString()
      .padStart(2, "0");
    const s = (seconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  if (isConnecting) {
    return (
      <div className="flex items-center gap-2 text-krishirin-warning">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span className="text-sm font-medium">Connecting...</span>
      </div>
    );
  }

  if (isConnected) {
    return (
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 bg-red-600 text-white px-2.5 py-1 rounded-full text-xs font-bold animate-live-pulse">
          <Phone className="w-3 h-3" />
          LIVE
        </div>
        <span className="text-sm font-mono text-krishirin-text-muted">
          {formatTime(duration)}
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-krishirin-text-muted">
      <PhoneOff className="w-4 h-4" />
      <span className="text-sm">Not connected</span>
    </div>
  );
}
