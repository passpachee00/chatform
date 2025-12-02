"use client";

import { useState } from "react";
import type { ApplicationData } from "@/types";

type RuleStatus = "pending" | "pass" | "fail";

interface Rule {
  id: string;
  label: string;
  status: RuleStatus;
}

export default function MockForm() {
  const [formData, setFormData] = useState<ApplicationData>({
    currentAddress: "",
    occupation: "",
    jobTitle: "",
    companyName: "",
    companyAddress: "",
    monthlyIncome: undefined,
    incomeSource: "",
    currentAssets: undefined,
    countryIncomeSources: "",
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  const [rules, setRules] = useState<Rule[]>([
    // { id: "company_exists", label: "Company Existence Check", status: "pending" },
    { id: "distance_check", label: "Address Distance Check", status: "pending" },
    // { id: "income_plausibility", label: "Income Plausibility Check", status: "pending" },
    // { id: "contradictions", label: "Field Contradictions Check", status: "pending" },
  ]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      // Call backend API
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${API_URL}/api/validate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error("Validation failed");
      }

      const result = await response.json();
      console.log("Validation result:", result);

      // Update rule statuses based on red flags
      setRules((prevRules) =>
        prevRules.map((rule) => {
          const hasFlag = result.red_flags.some(
            (flag: any) => flag.rule === rule.id
          );
          return {
            ...rule,
            status: hasFlag ? "fail" : "pass",
          };
        })
      );

      if (result.red_flags.length > 0) {
        alert(`Found ${result.red_flags.length} red flag(s). Check the validation rules below.`);
      } else {
        alert("All validation checks passed! ✅");
      }
    } catch (error) {
      console.error("Error validating application:", error);
      alert("Error validating application. Check console for details.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]:
        name === "monthlyIncome" || name === "currentAssets"
          ? value === ""
            ? undefined
            : Number(value)
          : value,
    }));
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl mx-auto space-y-8">
      {/* Personal Info Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold text-black">
          Personal Information
        </h2>
        <div>
          <label
            htmlFor="currentAddress"
            className="block text-sm font-medium text-black mb-1"
          >
            Current Address
          </label>
          <input
            type="text"
            id="currentAddress"
            name="currentAddress"
            value={formData.currentAddress}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
            placeholder="123 Main St, City, Country"
          />
        </div>
      </section>

      {/* Job Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold text-black">
          Employment Information
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label
              htmlFor="occupation"
              className="block text-sm font-medium text-black mb-1"
            >
              Occupation
            </label>
            <input
              type="text"
              id="occupation"
              name="occupation"
              value={formData.occupation}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
              placeholder="e.g., Software Engineer"
            />
          </div>
          <div>
            <label
              htmlFor="jobTitle"
              className="block text-sm font-medium text-black mb-1"
            >
              Job Title
            </label>
            <input
              type="text"
              id="jobTitle"
              name="jobTitle"
              value={formData.jobTitle}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
              placeholder="e.g., Senior Developer"
            />
          </div>
        </div>
        <div>
          <label
            htmlFor="companyName"
            className="block text-sm font-medium text-black mb-1"
          >
            Company Name
          </label>
          <input
            type="text"
            id="companyName"
            name="companyName"
            value={formData.companyName}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
            placeholder="e.g., Tech Corp"
          />
        </div>
        <div>
          <label
            htmlFor="companyAddress"
            className="block text-sm font-medium text-black mb-1"
          >
            Company Address
          </label>
          <input
            type="text"
            id="companyAddress"
            name="companyAddress"
            value={formData.companyAddress}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
            placeholder="456 Office Rd, City, Country"
          />
        </div>
      </section>

      {/* Income Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold text-black">
          Income Information
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label
              htmlFor="incomeSource"
              className="block text-sm font-medium text-black mb-1"
            >
              Source of Income
            </label>
            <input
              type="text"
              id="incomeSource"
              name="incomeSource"
              value={formData.incomeSource}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
              placeholder="e.g., Employment, Business"
            />
          </div>
          <div>
            <label
              htmlFor="monthlyIncome"
              className="block text-sm font-medium text-black mb-1"
            >
              Monthly Income
            </label>
            <input
              type="number"
              id="monthlyIncome"
              name="monthlyIncome"
              value={formData.monthlyIncome ?? ""}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              placeholder="e.g., 50000"
            />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label
              htmlFor="currentAssets"
              className="block text-sm font-medium text-black mb-1"
            >
              Current Assets
            </label>
            <input
              type="number"
              id="currentAssets"
              name="currentAssets"
              value={formData.currentAssets ?? ""}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              placeholder="e.g., 100000"
            />
          </div>
          <div>
            <label
              htmlFor="countryIncomeSources"
              className="block text-sm font-medium text-black mb-1"
            >
              Country Income Sources
            </label>
            <input
              type="text"
              id="countryIncomeSources"
              name="countryIncomeSources"
              value={formData.countryIncomeSources}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
              placeholder="e.g., Thailand, Singapore"
            />
          </div>
        </div>
      </section>

      {/* Submit Button */}
      <div className="flex justify-end">
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting ? "Submitting..." : "Submit Application"}
        </button>
      </div>

      {/* Validation Rules Status */}
      <div className="mt-8 pt-8 border-t border-gray-200">
        <h3 className="text-lg font-semibold text-black mb-4">
          Validation Rules
        </h3>
        <div className="space-y-3">
          {rules.map((rule) => (
            <div
              key={rule.id}
              className="flex items-center gap-3 p-3 rounded-lg bg-gray-50"
            >
              {/* Traffic Light Indicator */}
              <div
                className={`w-4 h-4 rounded-full flex-shrink-0 ${
                  rule.status === "pending"
                    ? "bg-gray-400"
                    : rule.status === "pass"
                    ? "bg-green-500"
                    : "bg-red-500"
                }`}
              />
              {/* Rule Label */}
              <span className="text-sm text-black">{rule.label}</span>
            </div>
          ))}
        </div>
      </div>
    </form>
  );
}
