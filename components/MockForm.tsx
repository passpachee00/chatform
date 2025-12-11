"use client";

import { useState, useMemo } from "react";
import type { ApplicationData, RedFlag, PreScreeningData, ChatMessage } from "@/types";
import ChatBot from "./ChatBot";
import { PreScreeningSection } from "./PreScreeningSection";
import { PreScreeningChatModal } from "./PreScreeningChatModal";

type RuleStatus = "pending" | "pass" | "fail";

interface Rule {
  id: string;
  label: string;
  status: RuleStatus;
  debugInfo?: any;
  redFlag?: RedFlag;
}

export default function MockForm() {
  const [formData, setFormData] = useState<ApplicationData>({
    firstName: "",
    lastName: "",
    currentAddress: "",
    employmentType: "",
    jobTitle: "",
    companyName: "",
    companyAddress: "",
    companyWebsite: "",
    monthlyIncome: undefined,
    sourceOfFunds: "",
    currentAssets: undefined,
    countryIncomeSources: "",
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  const [rules, setRules] = useState<Rule[]>([
    { id: "blacklist_check", label: "Blacklist Name Check", status: "pending" },
    { id: "employer_verification_check", label: "Employer Verification", status: "pending" },
    { id: "distance_check", label: "Address Distance Check", status: "pending" },
    { id: "political_exposure_check", label: "Political Exposure Check", status: "pending" },
    { id: "source_of_funds_alignment_check", label: "Source of Funds Alignment", status: "pending" },
    // { id: "company_exists", label: "Company Existence Check", status: "pending" },
    // { id: "income_plausibility", label: "Income Plausibility Check", status: "pending" },
    // { id: "contradictions", label: "Field Contradictions Check", status: "pending" },
  ]);

  const [activeRedFlag, setActiveRedFlag] = useState<RedFlag | null>(null);

  const [preScreeningData, setPreScreeningData] = useState<PreScreeningData>({
    answered: false,
    response: null,
    explanation: "",
    chatHistory: [],
  });

  const [isPreScreeningChatOpen, setIsPreScreeningChatOpen] = useState(false);

  // Stabilize object references to prevent chat from resetting
  const stableRedFlag = useMemo(() => activeRedFlag, [activeRedFlag?.rule]);
  const stableFormData = useMemo(() => formData, [
    formData.firstName,
    formData.lastName,
    formData.currentAddress,
    formData.employmentType,
    formData.jobTitle,
    formData.companyName,
    formData.companyAddress,
    formData.companyWebsite,
    formData.monthlyIncome,
    formData.sourceOfFunds,
    formData.currentAssets,
    formData.countryIncomeSources,
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
        body: JSON.stringify({
          ...formData,
          // Add pre-screening data
          preScreening: preScreeningData.answered
            ? {
                response: preScreeningData.response,
                explanation: preScreeningData.explanation,
                chatHistory: preScreeningData.chatHistory,
              }
            : null,
        }),
      });

      if (!response.ok) {
        throw new Error("Validation failed");
      }

      const result = await response.json();
      console.log("Validation result:", result);

      // Update rule statuses based on red flags
      setRules((prevRules) =>
        prevRules.map((rule) => {
          const flag = result.red_flags.find(
            (f: any) => f.rule === rule.id
          );
          return {
            ...rule,
            status: flag ? "fail" : "pass",
            debugInfo: flag?.debugInfo || null,
            redFlag: flag || undefined,
          };
        })
      );

      // Validation complete - results shown in traffic lights below
    } catch (error) {
      console.error("Error validating application:", error);
      alert("Error validating application. Check console for details.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
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

  const handlePreScreeningResponse = (response: "yes" | "no") => {
    if (response === "no") {
      setPreScreeningData({
        answered: true,
        response: "no",
        explanation: "",
        chatHistory: [],
      });
    } else {
      // Open chat modal for explanation
      setIsPreScreeningChatOpen(true);
    }
  };

  const handlePreScreeningChatComplete = (
    explanation: string,
    chatHistory: ChatMessage[]
  ) => {
    setPreScreeningData({
      answered: true,
      response: "yes",
      explanation,
      chatHistory,
    });
    setIsPreScreeningChatOpen(false);
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl mx-auto space-y-8">
      {/* Personal Info Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold text-black">
          Personal Information
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label
              htmlFor="firstName"
              className="block text-sm font-medium text-black mb-1"
            >
              First Name
            </label>
            <input
              type="text"
              id="firstName"
              name="firstName"
              value={formData.firstName}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
              placeholder="John"
            />
          </div>
          <div>
            <label
              htmlFor="lastName"
              className="block text-sm font-medium text-black mb-1"
            >
              Last Name
            </label>
            <input
              type="text"
              id="lastName"
              name="lastName"
              value={formData.lastName}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
              placeholder="Doe"
            />
          </div>
        </div>
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
              htmlFor="employmentType"
              className="block text-sm font-medium text-black mb-1"
            >
              Employment Type
            </label>
            <select
              id="employmentType"
              name="employmentType"
              value={formData.employmentType}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black bg-white"
            >
              <option value="">-- Select Employment Type --</option>
              <option value="Business Owner">Business Owner</option>
              <option value="Government Officer">Government Officer</option>
              <option value="Self-Employed">Self-Employed</option>
              <option value="State Enterprise Officer">State Enterprise Officer</option>
              <option value="Freelancer">Freelancer</option>
              <option value="Student">Student</option>
              <option value="Company Employee">Company Employee</option>
              <option value="Politician">Politician</option>
              <option value="Unemployed">Unemployed</option>
            </select>
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
        <div>
          <label
            htmlFor="companyWebsite"
            className="block text-sm font-medium text-black mb-1"
          >
            Company Website (Optional)
          </label>
          <input
            type="url"
            id="companyWebsite"
            name="companyWebsite"
            value={formData.companyWebsite}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
            placeholder="https://example.com"
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
              htmlFor="sourceOfFunds"
              className="block text-sm font-medium text-black mb-1"
            >
              Source of Funds
            </label>
            <select
              id="sourceOfFunds"
              name="sourceOfFunds"
              value={formData.sourceOfFunds}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black bg-white"
            >
              <option value="">-- Select Source of Funds --</option>
              <option value="Salary">Salary</option>
              <option value="Business Income">Business Income</option>
              <option value="Inheritance">Inheritance</option>
              <option value="Savings">Savings</option>
              <option value="Investments">Investments</option>
              <option value="Pension">Pension</option>
            </select>
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

      {/* Pre-Screening Section */}
      <PreScreeningSection
        data={preScreeningData}
        onResponseChange={handlePreScreeningResponse}
        onChatComplete={handlePreScreeningChatComplete}
      />

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
            <div key={rule.id} className="space-y-2">
              <div className="flex items-center gap-3 p-3 rounded-lg bg-gray-50">
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
                <span className="text-sm text-black flex-1">{rule.label}</span>

                {/* Fix It Button */}
                {rule.status === "fail" && rule.redFlag && (
                  <button
                    onClick={() => setActiveRedFlag(rule.redFlag!)}
                    className="px-3 py-1 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
                  >
                    Fix It
                  </button>
                )}
              </div>

              {/* Debug Info Box */}
              {rule.debugInfo && (
                <div className="ml-7 p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-black">
                  <div className="font-semibold mb-2">Debug Information:</div>
                  {rule.debugInfo.currentAddress && (
                    <div className="mb-1">
                      <span className="font-medium">Current Address:</span>{" "}
                      {rule.debugInfo.currentAddress.address}
                      {rule.debugInfo.currentAddress.lat !== null &&
                       rule.debugInfo.currentAddress.lng !== null ? (
                        <span className="text-gray-600">
                          {" "}
                          (lat: {rule.debugInfo.currentAddress.lat.toFixed(6)}, lng:{" "}
                          {rule.debugInfo.currentAddress.lng.toFixed(6)})
                        </span>
                      ) : (
                        <span className="text-red-600 text-xs">
                          {" "}[Google: {rule.debugInfo.currentAddress.google_status || "FAILED"}]
                        </span>
                      )}
                    </div>
                  )}
                  {rule.debugInfo.companyAddress && (
                    <div className="mb-1">
                      <span className="font-medium">Company Address:</span>{" "}
                      {rule.debugInfo.companyAddress.address}
                      {rule.debugInfo.companyAddress.lat !== null &&
                       rule.debugInfo.companyAddress.lng !== null ? (
                        <span className="text-gray-600">
                          {" "}
                          (lat: {rule.debugInfo.companyAddress.lat.toFixed(6)}, lng:{" "}
                          {rule.debugInfo.companyAddress.lng.toFixed(6)})
                        </span>
                      ) : (
                        <span className="text-red-600 text-xs">
                          {" "}[Google: {rule.debugInfo.companyAddress.google_status || "FAILED"}]
                        </span>
                      )}
                    </div>
                  )}
                  {rule.debugInfo.distance_km !== undefined && (
                    <div className="mb-1">
                      <span className="font-medium">Distance:</span>{" "}
                      {rule.debugInfo.distance_km !== null ? (
                        <span>{rule.debugInfo.distance_km.toFixed(2)} km</span>
                      ) : (
                        <span className="text-red-600 text-xs">N/A (geocoding failed)</span>
                      )}
                    </div>
                  )}
                  {rule.debugInfo.perplexity_details && (
                    <div className="mt-2 pt-2 border-t border-blue-300">
                      <div className="font-medium mb-1">Perplexity AI Verification:</div>
                      <div className="mb-1">
                        <span className="font-medium">Result:</span>{" "}
                        <span className={rule.debugInfo.perplexity_details.result === "YES" ? "text-green-600" : "text-red-600"}>
                          {rule.debugInfo.perplexity_details.result}
                        </span>
                      </div>
                      {rule.debugInfo.perplexity_details.explanation && (
                        <div className="mb-1">
                          <span className="font-medium">Explanation:</span>{" "}
                          {rule.debugInfo.perplexity_details.explanation}
                        </div>
                      )}
                      {rule.debugInfo.perplexity_details.closest_company_name && (
                        <div className="mb-1">
                          <span className="font-medium">Matched Company:</span>{" "}
                          {rule.debugInfo.perplexity_details.closest_company_name}
                        </div>
                      )}
                      {rule.debugInfo.perplexity_details.closest_company_website && (
                        <div>
                          <span className="font-medium">Website:</span>{" "}
                          <a
                            href={rule.debugInfo.perplexity_details.closest_company_website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline"
                          >
                            {rule.debugInfo.perplexity_details.closest_company_website}
                          </a>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ChatBot Modal - Always mounted to preserve conversation history */}
      <ChatBot
        redFlag={stableRedFlag || activeRedFlag || { rule: "", message: "", affectedFields: [] }}
        applicationData={stableFormData}
        isOpen={!!activeRedFlag}
        onClose={() => setActiveRedFlag(null)}
      />

      {/* Pre-screening Chat Modal */}
      <PreScreeningChatModal
        isOpen={isPreScreeningChatOpen}
        onClose={() => setIsPreScreeningChatOpen(false)}
        onComplete={handlePreScreeningChatComplete}
        initialHistory={preScreeningData.chatHistory}
      />
    </form>
  );
}
