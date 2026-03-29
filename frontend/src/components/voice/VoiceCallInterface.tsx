"use client";

import {
  PipecatAppBase,
  SpinLoader,
  type PipecatBaseChildProps,
} from "@pipecat-ai/voice-ui-kit";
import { CallScreen } from "./CallScreen";

interface VoiceCallInterfaceProps {
  farmerId: string;
  callType: "understanding" | "advisory";
  sidePanel?: React.ReactNode;
  onCallEnd?: () => void;
}

export function VoiceCallInterface({
  farmerId,
  callType,
  sidePanel,
  onCallEnd,
}: VoiceCallInterfaceProps) {
  return (
    <PipecatAppBase
      transportType="smallwebrtc"
      connectParams={{
        webrtcUrl: `/api/offer?farmer_id=${encodeURIComponent(farmerId)}&call_type=${encodeURIComponent(callType)}`,
      }}
      transportOptions={{
        waitForICEGathering: true,
      }}
      clientOptions={{
        enableCam: false,
        enableMic: true,
      }}
      noThemeProvider
      initDevicesOnMount
    >
      {({
        client,
        handleConnect,
        handleDisconnect,
        error,
      }: PipecatBaseChildProps) =>
        !client ? (
          <div className="flex items-center justify-center h-full bg-gray-950">
            <SpinLoader />
          </div>
        ) : (
          <CallScreen
            handleConnect={handleConnect}
            handleDisconnect={async () => {
              await handleDisconnect?.();
              onCallEnd?.();
            }}
            error={error}
            callType={callType}
            sidePanel={sidePanel}
          />
        )
      }
    </PipecatAppBase>
  );
}
