import type {
  ApplicationStatus,
  PreCallBriefing,
  AgentPipelineStatus,
  AllResults,
  FarmerProfile,
} from "./types";

// Use empty string (relative URLs) by default so requests go through the
// Next.js rewrite proxy and work on any deployed host.  Set NEXT_PUBLIC_API_URL
// only when the backend is on a separate origin.
const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// ===== Application APIs =====

export async function createApplication(
  farmerData: Partial<FarmerProfile>
): Promise<{ farmer_id: string }> {
  return fetchJSON("/api/application", {
    method: "POST",
    body: JSON.stringify(farmerData),
  });
}

export async function uploadDocument(
  farmerId: string,
  file: File,
  docType: string
): Promise<{
  document_id: string;
  status: string;
  extracted_data?: Record<string, unknown>;
  confidence?: number;
}> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("doc_type", docType);
  formData.append("farmer_id", farmerId);

  const res = await fetch(`${API_URL}/api/documents/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`Upload failed: ${res.statusText}`);
  return res.json();
}

export async function triggerAnalysis(
  farmerId: string
): Promise<{ status: string }> {
  return fetchJSON(`/api/application/${farmerId}/analyze`, {
    method: "POST",
  });
}

export async function getApplicationStatus(
  farmerId: string
): Promise<ApplicationStatus> {
  return fetchJSON(`/api/application/${farmerId}/status`);
}

// ===== Pre-Call Briefing =====

export async function getPreCallBriefing(
  farmerId: string
): Promise<PreCallBriefing> {
  return fetchJSON(`/api/application/${farmerId}/briefing`);
}

// ===== Agent Pipeline =====

export async function markCall1Complete(
  farmerId: string
): Promise<{ status: string }> {
  return fetchJSON(`/api/application/${farmerId}/call1-complete`, {
    method: "POST",
  });
}

export async function getPipelineStatus(
  farmerId: string
): Promise<AgentPipelineStatus> {
  return fetchJSON(`/api/application/${farmerId}/pipeline-status`);
}

// ===== Results =====

export async function getResults(farmerId: string): Promise<AllResults> {
  return fetchJSON(`/api/application/${farmerId}/results`);
}

export async function getTranscripts(
  farmerId: string
): Promise<{ call1: string; call2: string }> {
  return fetchJSON(`/api/application/${farmerId}/transcripts`);
}
