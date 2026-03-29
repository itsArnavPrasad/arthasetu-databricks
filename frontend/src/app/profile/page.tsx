"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { FarmerInfoForm } from "@/components/apply/FarmerInfoForm";
import { DocumentUpload } from "@/components/apply/DocumentUpload";
import { useApplication } from "@/context/ApplicationContext";
import { createApplication, uploadDocument, triggerAnalysis } from "@/lib/api";
import type { DocumentInfo, FarmerProfile } from "@/lib/types";
import {
  ArrowLeft,
  User,
  FileText,
  CheckCircle2,
  Sprout,
  Brain,
  Loader2,
} from "lucide-react";

type Tab = "details" | "documents";

/** Merge OCR-extracted data into the farmer profile based on document type. */
function mergeExtractedData(
  current: Partial<FarmerProfile>,
  extracted: Record<string, unknown>,
  docType: string
): Partial<FarmerProfile> {
  const merged: Partial<FarmerProfile> = {};

  switch (docType) {
    case "aadhaar":
      if (extracted.name) merged.name = extracted.name as string;
      if (extracted.aadhaar_last4) merged.aadhaar_last4 = extracted.aadhaar_last4 as string;
      if (extracted.district && !current.district) merged.district = extracted.district as string;
      if (extracted.state && !current.state) merged.state = extracted.state as string;
      break;

    case "land_record":
      if (extracted.area_acres) merged.land_holding_acres = extracted.area_acres as number;
      if (extracted.land_type) merged.land_type = extracted.land_type as string;
      if (extracted.district) merged.district = extracted.district as string;
      if (extracted.irrigation_source) merged.irrigation_type = extracted.irrigation_source as string;
      break;

    case "bank_statement": {
      const summary = extracted.summary as Record<string, unknown> | undefined;
      if (summary) {
        merged.bank_summary = {
          ...(current.bank_summary || {}),
          avg_monthly_income: summary.total_credits
            ? Math.round((summary.total_credits as number) / 12)
            : undefined,
          avg_monthly_expense: summary.total_debits
            ? Math.round((summary.total_debits as number) / 12)
            : undefined,
          avg_balance: summary.avg_balance as number | undefined,
        };
      }
      break;
    }

    case "loan_slip":
      if (extracted.loan_amount || extracted.lender) {
        const loan = {
          type: (extracted.loan_type as string) || "unknown",
          amount: extracted.loan_amount as number | undefined,
          outstanding: extracted.outstanding_amount as number | undefined,
          emi: extracted.emi_amount as number | undefined,
          status: (extracted.status as string) || "active",
          lender: extracted.lender as string | undefined,
        };
        merged.existing_loans = [...(current.existing_loans || []), loan];
      }
      break;

    case "crop_receipt":
      if (extracted.crop_name) {
        const cropName = extracted.crop_name as string;
        const existingCrops = current.crops || [];
        if (!existingCrops.some((c) => c.toLowerCase() === cropName.toLowerCase())) {
          merged.crops = [...existingCrops, cropName];
        }
      }
      break;
  }

  return merged;
}

export default function ProfilePage() {
  const router = useRouter();
  const {
    farmerId,
    setFarmerId,
    setFarmerProfile,
    farmerProfile,
    documents,
    addDocument,
    updateDocument,
    removeDocument,
  } = useApplication();
  const [activeTab, setActiveTab] = useState<Tab>("details");
  const [saved, setSaved] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  const handleInfoSubmit = async (data: Partial<FarmerProfile>) => {
    setFarmerProfile(data);
    try {
      if (!farmerId) {
        const { farmer_id } = await createApplication(data);
        setFarmerId(farmer_id);
      }
    } catch {
      setFarmerId(`demo_farmer_${Date.now()}`);
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleUpload = useCallback(
    async (file: File, docType: string) => {
      // Ensure we have a real farmer_id before uploading
      let currentFarmerId = farmerId;
      if (!currentFarmerId) {
        try {
          const { farmer_id } = await createApplication(farmerProfile || {});
          setFarmerId(farmer_id);
          currentFarmerId = farmer_id;
        } catch {
          currentFarmerId = `demo_farmer_${Date.now()}`;
          setFarmerId(currentFarmerId);
        }
      }

      const tempId = `doc_${Date.now()}`;
      const newDoc: DocumentInfo = {
        id: tempId,
        type: docType as DocumentInfo["type"],
        filename: file.name,
        status: "uploading",
        uploadedAt: new Date().toISOString(),
      };
      addDocument(newDoc);

      try {
        const result = await uploadDocument(currentFarmerId, file, docType);
        const newStatus = result.status === "verified" ? "verified" as const : "uploaded" as const;
        updateDocument(tempId, {
          id: result.document_id,
          status: newStatus,
        });

        // Merge OCR-extracted data into farmer profile
        if (result.extracted_data && Object.keys(result.extracted_data).length > 0) {
          const extracted = result.extracted_data as Record<string, unknown>;
          setFarmerProfile({
            ...farmerProfile,
            ...mergeExtractedData(farmerProfile || {}, extracted, docType),
          });
        }
      } catch {
        updateDocument(tempId, { status: "error" as const });
      }
    },
    [farmerId, farmerProfile, setFarmerProfile, addDocument, updateDocument]
  );

  const handleRemove = (docId: string) => {
    removeDocument(docId);
  };

  const handleAnalyze = async () => {
    if (!farmerId) return;
    setAnalyzing(true);
    try {
      await triggerAnalysis(farmerId);
      router.push("/");
    } catch (e) {
      console.error("Analysis trigger failed:", e);
    } finally {
      setAnalyzing(false);
    }
  };

  const verifiedCount = documents.filter((d) => d.status === "verified").length;
  const hasAnyDocs = documents.length > 0;

  return (
    <div className="min-h-screen bg-krishirin-bg">
      {/* Header */}
      <header className="bg-white border-b border-krishirin-border">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center gap-3">
          <button
            onClick={() => router.push("/")}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-krishirin-text" />
          </button>
          <div className="flex items-center gap-2">
            <Sprout className="w-5 h-5 text-krishirin-primary" />
            <h1 className="font-semibold text-krishirin-text">Profile & Documents</h1>
          </div>
          {saved && (
            <span className="ml-auto flex items-center gap-1 text-xs text-krishirin-success font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" /> Saved
            </span>
          )}
        </div>
      </header>

      {/* Tabs */}
      <div className="max-w-3xl mx-auto px-4">
        <div className="flex border-b border-krishirin-border mt-2">
          <button
            onClick={() => setActiveTab("details")}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === "details"
                ? "text-krishirin-primary border-b-2 border-krishirin-primary"
                : "text-krishirin-text-muted hover:text-krishirin-text"
            }`}
          >
            <User className="w-4 h-4" />
            Farmer Details
          </button>
          <button
            onClick={() => setActiveTab("documents")}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === "documents"
                ? "text-krishirin-primary border-b-2 border-krishirin-primary"
                : "text-krishirin-text-muted hover:text-krishirin-text"
            }`}
          >
            <FileText className="w-4 h-4" />
            Documents
            {documents.length > 0 && (
              <span className="bg-krishirin-primary text-white text-xs w-5 h-5 rounded-full flex items-center justify-center">
                {documents.length}
              </span>
            )}
          </button>
        </div>

        {/* Content */}
        <div className="py-6">
          {activeTab === "details" && (
            <FarmerInfoForm
              onSubmit={handleInfoSubmit}
              initialData={farmerProfile || undefined}
            />
          )}
          {activeTab === "documents" && (
            <>
              <DocumentUpload
                documents={documents}
                onUpload={handleUpload}
                onRemove={handleRemove}
              />

              {/* Analyze Button */}
              <div className="mt-8 border-t border-krishirin-border pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-krishirin-text">
                      {verifiedCount} of {documents.length} document{documents.length !== 1 ? "s" : ""} verified
                    </p>
                    <p className="text-xs text-krishirin-text-muted mt-0.5">
                      {hasAnyDocs
                        ? "You can analyze with available documents. Missing documents will be noted."
                        : "Upload at least one document to begin analysis."}
                    </p>
                  </div>
                  <button
                    onClick={handleAnalyze}
                    disabled={!hasAnyDocs || analyzing || !farmerId}
                    className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold transition-all ${
                      hasAnyDocs && !analyzing && farmerId
                        ? "bg-krishirin-primary text-white hover:bg-krishirin-primary/90 shadow-md hover:shadow-lg"
                        : "bg-gray-200 text-gray-400 cursor-not-allowed"
                    }`}
                  >
                    {analyzing ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Brain className="w-4 h-4" />
                        Analyze & Score
                      </>
                    )}
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
