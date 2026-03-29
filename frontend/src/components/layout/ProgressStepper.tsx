"use client";

import { useApplication } from "@/context/ApplicationContext";
import type { ApplicationPhase } from "@/lib/types";
import {
  FileText,
  Phone,
  Brain,
  PhoneCall,
  CheckCircle2,
} from "lucide-react";

const steps: { phase: ApplicationPhase; label: string; icon: React.ElementType }[] = [
  { phase: "apply", label: "Apply", icon: FileText },
  { phase: "call1", label: "Call 1", icon: Phone },
  { phase: "processing", label: "Strategy", icon: Brain },
  { phase: "call2", label: "Call 2", icon: PhoneCall },
  { phase: "summary", label: "Summary", icon: CheckCircle2 },
];

const phaseOrder: ApplicationPhase[] = [
  "apply",
  "analysis",
  "call1",
  "processing",
  "call2",
  "summary",
];

export function ProgressStepper() {
  const { phase } = useApplication();
  const currentIndex = phaseOrder.indexOf(phase);

  return (
    <div className="flex items-center justify-center gap-1 py-3 px-4 bg-krishirin-surface border-b border-krishirin-border">
      {steps.map((step, i) => {
        const stepIndex = phaseOrder.indexOf(step.phase);
        const isActive = step.phase === phase || (phase === "analysis" && step.phase === "apply");
        const isCompleted = stepIndex < currentIndex;
        const Icon = step.icon;

        return (
          <div key={step.phase} className="flex items-center">
            <div
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                isActive
                  ? "bg-krishirin-primary text-white"
                  : isCompleted
                    ? "bg-krishirin-primary-light/20 text-krishirin-primary"
                    : "bg-gray-100 text-krishirin-text-muted"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{step.label}</span>
            </div>
            {i < steps.length - 1 && (
              <div
                className={`w-6 h-0.5 mx-1 ${
                  isCompleted ? "bg-krishirin-primary-light" : "bg-gray-200"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
