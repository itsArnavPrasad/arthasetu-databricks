"use client";

import { useState, useCallback } from "react";
import type { DocumentInfo } from "@/lib/types";
import {
  Upload,
  FileText,
  CheckCircle2,
  AlertCircle,
  Loader2,
  X,
  Plus,
} from "lucide-react";

const DOC_TYPES = [
  { key: "aadhaar", label: "Aadhaar Card", desc: "Identity proof", multiple: false },
  { key: "bank_statement", label: "Bank Statement", desc: "Last 6-12 months", multiple: true },
  { key: "loan_slip", label: "Loan Document", desc: "Sanction letter / passbook", multiple: true },
  { key: "land_record", label: "Land Record", desc: "7/12 extract or 8A", multiple: true },
  { key: "crop_receipt", label: "Crop Receipt / Mandi Slip", desc: "Previous sales", multiple: true },
] as const;

interface DocumentUploadProps {
  documents: DocumentInfo[];
  onUpload: (file: File, docType: string) => Promise<void>;
  onRemove: (docId: string) => void;
}

export function DocumentUpload({
  documents,
  onUpload,
  onRemove,
}: DocumentUploadProps) {
  const [dragOver, setDragOver] = useState<string | null>(null);

  const handleDrop = useCallback(
    async (e: React.DragEvent, docType: string) => {
      e.preventDefault();
      setDragOver(null);
      const file = e.dataTransfer.files[0];
      if (file) await onUpload(file, docType);
    },
    [onUpload]
  );

  const handleFileInput = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>, docType: string) => {
      const file = e.target.files?.[0];
      if (file) await onUpload(file, docType);
      e.target.value = "";
    },
    [onUpload]
  );

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-krishirin-text">
        Upload Documents
      </h2>
      <p className="text-sm text-krishirin-text-muted">
        Upload your documents for loan assessment. Supported: PDF, JPG, PNG.
        You can upload multiple files for land records, bank statements, and loan documents.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {DOC_TYPES.map(({ key, label, desc, multiple }) => {
          const uploaded = documents.filter((d) => d.type === key);
          const isDragOver = dragOver === key;
          const hasAtLeastOne = uploaded.length > 0;
          const allVerified = hasAtLeastOne && uploaded.every((d) => d.status === "verified");

          return (
            <div
              key={key}
              className={`border-2 border-dashed rounded-xl p-4 transition-colors ${
                isDragOver
                  ? "border-krishirin-primary bg-krishirin-primary/5"
                  : allVerified
                  ? "border-krishirin-success/40 bg-krishirin-success/5"
                  : "border-krishirin-border hover:border-krishirin-primary-light"
              }`}
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(key);
              }}
              onDragLeave={() => setDragOver(null)}
              onDrop={(e) => handleDrop(e, key)}
            >
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h3 className="font-medium text-sm text-krishirin-text">
                    {label}
                    {multiple && (
                      <span className="ml-1.5 text-[10px] text-krishirin-text-muted font-normal">
                        (multiple allowed)
                      </span>
                    )}
                  </h3>
                  <p className="text-xs text-krishirin-text-muted">{desc}</p>
                </div>
                {allVerified && (
                  <CheckCircle2 className="w-5 h-5 text-krishirin-success shrink-0" />
                )}
              </div>

              {/* Uploaded files list */}
              {uploaded.length > 0 && (
                <div className="space-y-2 mb-2">
                  {uploaded.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-2"
                    >
                      <FileText className="w-4 h-4 text-krishirin-primary shrink-0" />
                      <span className="text-xs truncate flex-1">
                        {doc.filename}
                      </span>
                      <StatusBadge status={doc.status} />
                      <button
                        onClick={() => onRemove(doc.id)}
                        className="text-gray-400 hover:text-red-500"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Upload area — show if no file yet, or if multiple allowed */}
              {(uploaded.length === 0 || multiple) && (
                <label className="flex items-center gap-2 cursor-pointer py-2 px-3 rounded-lg hover:bg-gray-50 transition-colors">
                  {uploaded.length === 0 ? (
                    <>
                      <Upload className="w-6 h-6 text-krishirin-text-muted" />
                      <span className="text-xs text-krishirin-text-muted">
                        Drag & drop or click to upload
                      </span>
                    </>
                  ) : (
                    <>
                      <Plus className="w-4 h-4 text-krishirin-primary" />
                      <span className="text-xs text-krishirin-primary font-medium">
                        Add another {label.toLowerCase()}
                      </span>
                    </>
                  )}
                  <input
                    type="file"
                    className="hidden"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={(e) => handleFileInput(e, key)}
                  />
                </label>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: DocumentInfo["status"] }) {
  switch (status) {
    case "uploading":
      return (
        <span className="flex items-center gap-1 text-xs text-blue-600">
          <Loader2 className="w-3 h-3 animate-spin" /> Uploading
        </span>
      );
    case "uploaded":
    case "processing":
      return (
        <span className="flex items-center gap-1 text-xs text-amber-600">
          <Loader2 className="w-3 h-3 animate-spin" /> Processing
        </span>
      );
    case "verified":
      return (
        <span className="flex items-center gap-1 text-xs text-krishirin-success">
          <CheckCircle2 className="w-3 h-3" /> Verified
        </span>
      );
    case "error":
      return (
        <span className="flex items-center gap-1 text-xs text-red-600">
          <AlertCircle className="w-3 h-3" /> Error
        </span>
      );
  }
}
