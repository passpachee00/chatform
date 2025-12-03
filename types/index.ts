// Application data structure
export interface ApplicationData {
  // Personal Info
  currentAddress?: string;

  // Job Section
  occupation?: string;
  jobTitle?: string;
  companyName?: string;
  companyAddress?: string;

  // Income Section
  monthlyIncome?: number;
  incomeSource?: string;
  currentAssets?: number;
  countryIncomeSources?: string;

  // System fields (added during resolution)
  justifications?: {
    [field: string]: string; // field -> explanation
  };
  correctedFields?: {
    [field: string]: {
      oldValue: string;
      newValue: string;
    };
  };
}

// Red flag structure
export interface RedFlag {
  rule: string; // Rule identifier (e.g., "company_exists")
  message: string; // Human-readable issue description
  severity?: "low" | "medium" | "high";
  affectedFields: string[]; // Fields involved in the flag
  debugInfo?: any; // Debug information for troubleshooting
}

// Validation response from backend
export interface ValidationResponse {
  red_flags: RedFlag[];
}

// Chat message
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp?: Date;
}

// Chat resolution request
export interface ChatResolutionRequest {
  applicationData: ApplicationData;
  redFlags: RedFlag[];
}

// Chat resolution response
export interface ChatResolutionResponse {
  messages: ChatMessage[];
  status: "awaiting_response" | "resolved";
  updatedData?: ApplicationData;
  remainingFlags?: number;
}

// Chat message request
export interface ChatMessageRequest {
  sessionId: string;
  message: string;
  applicationData: ApplicationData;
  currentFlag: RedFlag;
}
