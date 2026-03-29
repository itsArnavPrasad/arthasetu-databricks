"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { VoiceCallInterface } from "@/components/voice/VoiceCallInterface";
import { LiveTranscript } from "@/components/voice/LiveTranscript";
import { useApplication } from "@/context/ApplicationContext";
import { markCall1Complete } from "@/lib/api";

export default function UnderstandingCallPage() {
  const router = useRouter();
  const { farmerId, setPhase } = useApplication();

  const activeFarmerId = farmerId || "";

  useEffect(() => {
    setPhase("call1");
  }, [setPhase]);

  const handleCallEnd = async () => {
    try {
      await markCall1Complete(activeFarmerId);
    } catch {
      // Backend might not be available in dev
    }
    router.push("/processing");
  };

  const sidePanel = (
    <LiveTranscript assistantLabel="KrishiRin AI" clientLabel="Farmer" />
  );

  return (
    <div className="h-screen flex flex-col">
      <VoiceCallInterface
        farmerId={activeFarmerId}
        callType="understanding"
        sidePanel={sidePanel}
        onCallEnd={handleCallEnd}
      />
    </div>
  );
}
