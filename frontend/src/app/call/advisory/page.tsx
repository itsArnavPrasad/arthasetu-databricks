"use client";

import { useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { VoiceCallInterface } from "@/components/voice/VoiceCallInterface";
import { AdvisoryTabPanel } from "@/components/voice/AdvisoryTabPanel";
import { useApplication } from "@/context/ApplicationContext";

export default function AdvisoryCallPage() {
  const router = useRouter();
  const { farmerId, setPhase } = useApplication();

  const activeFarmerId = farmerId || "";

  useEffect(() => {
    setPhase("call2");
  }, [setPhase]);

  const handleCallEnd = useCallback(() => {
    router.push("/summary");
  }, [router]);

  // Pass farmer_id as the SSE key — backend resolves to session_id internally
  const sidePanel = (
    <AdvisoryTabPanel sessionId={activeFarmerId} />
  );

  return (
    <div className="h-screen flex flex-col">
      <VoiceCallInterface
        farmerId={activeFarmerId}
        callType="advisory"
        sidePanel={sidePanel}
        onCallEnd={handleCallEnd}
      />
    </div>
  );
}
