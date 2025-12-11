// Application data structure
export interface ApplicationData {
  // Personal Info
  firstName?: string;
  lastName?: string;
  currentAddress?: string;

  // Job Section
  employmentType?: string;
  jobTitle?: string;
  companyName?: string;
  companyAddress?: string;
  companyWebsite?: string;

  // Income Section
  monthlyIncome?: number;
  sourceOfFunds?: string;
  currentAssets?: number;
  countryIncomeSources?: string;

  // Pre-screening data
  preScreening?: {
    response: "yes" | "no";
    explanation: string;
    chatHistory: ChatMessage[];
  } | null;

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

// Pre-screening data (for frontend state management)
export interface PreScreeningData {
  answered: boolean;
  response: "yes" | "no" | null;
  explanation: string;
  chatHistory: ChatMessage[];
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
  conversationHistory?: ChatMessage[];
}

// Chat session context (for frontend state management)
export interface ChatSessionContext {
  redFlag: RedFlag;
  applicationData: ApplicationData;
  conversationHistory: ChatMessage[];
}

// Chat API request payload (simplified for frontend use)
export interface ChatMessagePayload {
  message: string;
  redFlag: RedFlag;
  applicationData: ApplicationData;
  conversationHistory: ChatMessage[];
}

// Chat API response
export interface ChatMessageResponse {
  role: "assistant";
  content: string;
  timestamp: Date;
  status: "success" | "error";
  error?: string;
}
