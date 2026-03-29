"use client";

import { Header } from "./Header";
import { ProgressStepper } from "./ProgressStepper";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header />
      <ProgressStepper />
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
