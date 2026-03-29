"use client";

import { ThemeProvider } from "@pipecat-ai/voice-ui-kit";
import { ApplicationProvider } from "@/context/ApplicationContext";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider defaultTheme="light" disableStorage>
      <ApplicationProvider>{children}</ApplicationProvider>
    </ThemeProvider>
  );
}
