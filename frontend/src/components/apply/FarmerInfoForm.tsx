"use client";

import { useState } from "react";
import type { FarmerProfile } from "@/lib/types";

interface FarmerInfoFormProps {
  onSubmit: (data: Partial<FarmerProfile>) => void;
  initialData?: Partial<FarmerProfile>;
}

const STATES = [
  "Maharashtra", "Madhya Pradesh", "Uttar Pradesh", "Rajasthan",
  "Karnataka", "Gujarat", "Bihar", "Tamil Nadu", "Andhra Pradesh",
  "Telangana", "Punjab", "Haryana", "Odisha", "West Bengal",
];

const CROPS = [
  "Rice", "Wheat", "Soybean", "Cotton", "Sugarcane", "Chana",
  "Moong", "Toor", "Maize", "Jowar", "Bajra", "Groundnut",
  "Onion", "Tomato", "Potato",
];

export function FarmerInfoForm({ onSubmit, initialData }: FarmerInfoFormProps) {
  const [form, setForm] = useState({
    name: initialData?.name || "",
    aadhaar_last4: initialData?.aadhaar_last4 || "",
    district: initialData?.district || "",
    state: initialData?.state || "Maharashtra",
    land_holding_acres: initialData?.land_holding_acres || 0,
    land_type: initialData?.land_type || "owned" as const,
    crops: initialData?.crops || [] as string[],
  });

  const toggleCrop = (crop: string) => {
    setForm((f) => ({
      ...f,
      crops: f.crops.includes(crop)
        ? f.crops.filter((c) => c !== crop)
        : [...f.crops, crop],
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <h2 className="text-lg font-semibold text-krishirin-text">
        Farmer Details
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-krishirin-text mb-1">
            Full Name / पूरा नाम
          </label>
          <input
            type="text"
            required
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            className="w-full px-3 py-2 border border-krishirin-border rounded-lg text-sm focus:ring-2 focus:ring-krishirin-primary focus:border-transparent outline-none"
            placeholder="Enter farmer's name"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-krishirin-text mb-1">
            Aadhaar (Last 4 digits)
          </label>
          <input
            type="text"
            required
            maxLength={4}
            pattern="[0-9]{4}"
            value={form.aadhaar_last4}
            onChange={(e) =>
              setForm((f) => ({ ...f, aadhaar_last4: e.target.value }))
            }
            className="w-full px-3 py-2 border border-krishirin-border rounded-lg text-sm focus:ring-2 focus:ring-krishirin-primary focus:border-transparent outline-none"
            placeholder="XXXX"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-krishirin-text mb-1">
            State / राज्य
          </label>
          <select
            value={form.state}
            onChange={(e) => setForm((f) => ({ ...f, state: e.target.value }))}
            className="w-full px-3 py-2 border border-krishirin-border rounded-lg text-sm focus:ring-2 focus:ring-krishirin-primary focus:border-transparent outline-none"
          >
            {STATES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-krishirin-text mb-1">
            District / जिला
          </label>
          <input
            type="text"
            required
            value={form.district}
            onChange={(e) =>
              setForm((f) => ({ ...f, district: e.target.value }))
            }
            className="w-full px-3 py-2 border border-krishirin-border rounded-lg text-sm focus:ring-2 focus:ring-krishirin-primary focus:border-transparent outline-none"
            placeholder="Enter district name"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-krishirin-text mb-1">
            Land Holding (acres) / भूमि
          </label>
          <input
            type="number"
            required
            min="0"
            step="0.01"
            value={form.land_holding_acres || ""}
            onChange={(e) =>
              setForm((f) => ({
                ...f,
                land_holding_acres: parseFloat(e.target.value) || 0,
              }))
            }
            className="w-full px-3 py-2 border border-krishirin-border rounded-lg text-sm focus:ring-2 focus:ring-krishirin-primary focus:border-transparent outline-none"
            placeholder="e.g., 3.5"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-krishirin-text mb-1">
            Land Type
          </label>
          <select
            value={form.land_type}
            onChange={(e) =>
              setForm((f) => ({
                ...f,
                land_type: e.target.value as "owned" | "leased" | "shared",
              }))
            }
            className="w-full px-3 py-2 border border-krishirin-border rounded-lg text-sm focus:ring-2 focus:ring-krishirin-primary focus:border-transparent outline-none"
          >
            <option value="owned">Owned / स्वामित्व</option>
            <option value="leased">Leased / पट्टे पर</option>
            <option value="shared">Shared / साझा</option>
          </select>
        </div>
      </div>

      {/* Crop Selection */}
      <div>
        <label className="block text-sm font-medium text-krishirin-text mb-2">
          Crops Grown / फसलें
        </label>
        <div className="flex flex-wrap gap-2">
          {CROPS.map((crop) => (
            <button
              key={crop}
              type="button"
              onClick={() => toggleCrop(crop)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                form.crops.includes(crop)
                  ? "bg-krishirin-primary text-white"
                  : "bg-gray-100 text-krishirin-text-muted hover:bg-gray-200"
              }`}
            >
              {crop}
            </button>
          ))}
        </div>
      </div>

      <button
        type="submit"
        className="w-full py-3 bg-krishirin-primary text-white rounded-lg font-medium hover:bg-krishirin-primary/90 transition-colors"
      >
        Save & Continue
      </button>
    </form>
  );
}
