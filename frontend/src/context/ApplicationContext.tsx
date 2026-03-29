"use client";

import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import type { ApplicationPhase, FarmerProfile, AllResults, DocumentInfo } from "@/lib/types";

interface ApplicationState {
  farmerId: string | null;
  phase: ApplicationPhase;
  farmerProfile: Partial<FarmerProfile> | null;
  documents: DocumentInfo[];
  results: AllResults | null;
}

interface ApplicationContextValue extends ApplicationState {
  setFarmerId: (id: string) => void;
  setPhase: (phase: ApplicationPhase) => void;
  setFarmerProfile: (profile: Partial<FarmerProfile>) => void;
  setDocuments: (docs: DocumentInfo[]) => void;
  addDocument: (doc: DocumentInfo) => void;
  updateDocument: (id: string, updates: Partial<DocumentInfo>) => void;
  removeDocument: (id: string) => void;
  setResults: (results: AllResults) => void;
  reset: () => void;
}

const STORAGE_KEY = "krishirin_app_state";

const initialState: ApplicationState = {
  farmerId: null,
  phase: "apply",
  farmerProfile: null,
  documents: [],
  results: null,
};

function loadPersistedState(): ApplicationState {
  if (typeof window === "undefined") return initialState;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return initialState;
    const parsed = JSON.parse(raw) as Partial<ApplicationState>;
    return {
      farmerId: parsed.farmerId ?? null,
      phase: parsed.phase ?? "apply",
      farmerProfile: parsed.farmerProfile ?? null,
      documents: parsed.documents ?? [],
      results: parsed.results ?? null,
    };
  } catch {
    return initialState;
  }
}

function persistState(state: ApplicationState) {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Storage full or unavailable — silently ignore
  }
}

const ApplicationContext = createContext<ApplicationContextValue | null>(null);

export function ApplicationProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [state, setState] = useState<ApplicationState>(initialState);
  const [hydrated, setHydrated] = useState(false);

  // Hydrate from sessionStorage on mount (client-side only)
  useEffect(() => {
    setState(loadPersistedState());
    setHydrated(true);
  }, []);

  // Persist to sessionStorage on every state change (after hydration)
  useEffect(() => {
    if (hydrated) {
      persistState(state);
    }
  }, [state, hydrated]);

  const setFarmerId = useCallback(
    (id: string) => setState((s) => ({ ...s, farmerId: id })),
    []
  );
  const setPhase = useCallback(
    (phase: ApplicationPhase) => setState((s) => ({ ...s, phase })),
    []
  );
  const setFarmerProfile = useCallback(
    (profile: Partial<FarmerProfile>) =>
      setState((s) => ({ ...s, farmerProfile: profile })),
    []
  );
  const setDocuments = useCallback(
    (docs: DocumentInfo[]) => setState((s) => ({ ...s, documents: docs })),
    []
  );
  const addDocument = useCallback(
    (doc: DocumentInfo) =>
      setState((s) => ({ ...s, documents: [...s.documents, doc] })),
    []
  );
  const updateDocument = useCallback(
    (id: string, updates: Partial<DocumentInfo>) =>
      setState((s) => ({
        ...s,
        documents: s.documents.map((d) =>
          d.id === id ? { ...d, ...updates } : d
        ),
      })),
    []
  );
  const removeDocument = useCallback(
    (id: string) =>
      setState((s) => ({
        ...s,
        documents: s.documents.filter((d) => d.id !== id),
      })),
    []
  );
  const setResults = useCallback(
    (results: AllResults) => setState((s) => ({ ...s, results })),
    []
  );
  const reset = useCallback(() => {
    setState(initialState);
    if (typeof window !== "undefined") {
      sessionStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  return (
    <ApplicationContext.Provider
      value={{
        ...state,
        setFarmerId,
        setPhase,
        setFarmerProfile,
        setDocuments,
        addDocument,
        updateDocument,
        removeDocument,
        setResults,
        reset,
      }}
    >
      {children}
    </ApplicationContext.Provider>
  );
}

export function useApplication() {
  const ctx = useContext(ApplicationContext);
  if (!ctx) {
    throw new Error("useApplication must be used within ApplicationProvider");
  }
  return ctx;
}
