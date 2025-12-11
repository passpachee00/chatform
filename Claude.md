# ChatForm - AI-Powered Form Validation System

## Project Overview

ChatForm is an intelligent form validation system that combines rule-based validation with AI-powered conversational resolution. The system collects applicant data, identifies potential red flags using a rule engine, and uses an interactive chatbot to resolve inconsistencies through natural conversation

### Core Components

1. **Mock Form (Next.js Frontend)** - Data collection interface
2. **Rule Engine (FastAPI Backend)** - Red flag detection system
3. **Interactive Chatbot (OpenAI GPT-4)** - Conversational red flag resolver

---

## System Architecture

```
┌─────────────────┐
│   Next.js UI    │
│  (Mock Form)    │
└────────┬────────┘
         │ POST /api/validate
         ▼
┌─────────────────┐
│  FastAPI Server │
│  Rule Engine    │
└────────┬────────┘
         │ red_flags[]
         ▼
┌─────────────────┐
│  ChatGPT Bot    │
│  (Sequential    │
│   Resolution)   │
└────────┬────────┘
         │ updated data
         ▼
┌─────────────────┐
│  Final Output   │
│  + Justifications│
└─────────────────┘
```

---

## Tech Stack

### Frontend
- **Framework**: Next.js 15+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (optional)
- **State Management**: React hooks (useState, useReducer)

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Server**: Uvicorn
- **LLM**: OpenAI GPT-4.1 / GPT-4.1-mini
- **HTTP Client**: httpx (for external API calls)

### Infrastructure
- **Frontend Deployment**: Vercel (https://chatform.vercel.app)
- **Backend Deployment**: Railway (https://chatform-production-236e.up.railway.app)
- **Database**: None (Phase 1 - in-memory only)
- **Architecture**: Split deployment - frontend and backend on separate platforms

---

## Folder Structure

```
chatform/
├── app/                          # Next.js App Router
│   ├── page.tsx                  # Home page with Mock Form
│   ├── layout.tsx                # Root layout
│   ├── globals.css               # Global styles
│   └── api/                      # API routes (optional proxy)
│       └── validate/
│           └── route.ts          # Proxy to FastAPI backend
│
├── components/                   # React components
│   ├── MockForm.tsx              # Main form component
│   ├── ChatInterface.tsx         # Chat UI for resolution
│   └── ui/                       # shadcn/ui components
│
├── lib/                          # Utilities
│   ├── api.ts                    # API client functions
│   └── types.ts                  # Shared TypeScript types
│
├── types/                        # TypeScript type definitions
│   └── index.ts                  # Application data types
│
├── hooks/                        # Custom React hooks
│   └── useFormValidation.ts      # Form state management
│
├── backend/                      # FastAPI application
│   ├── app/
│   │   ├── main.py               # FastAPI app entry point
│   │   ├── config.py             # Configuration settings
│   │   │
│   │   ├── routers/              # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── validation.py     # /validate endpoint
│   │   │   └── chat.py           # /chat endpoints
│   │   │
│   │   ├── services/             # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── rule_engine.py    # Red flag detection
│   │   │   ├── chat_service.py   # GPT-4 resolution logic
│   │   │   ├── employer_verification_service.py  # Company verification
│   │   │   └── tools/            # Tool calling handlers
│   │   │       ├── __init__.py
│   │   │       ├── base.py       # ToolHandler, ToolRegistry
│   │   │       └── employer_verification_tool.py
│   │   │
│   │   ├── models/               # Data models (future)
│   │   │
│   │   └── schemas/              # Pydantic schemas
│   │       ├── __init__.py
│   │       └── application.py    # Application data schemas
│   │
│   ├── tests/                    # Backend tests
│   │   ├── test_rule_engine.py
│   │   └── test_chatbot.py
│   │
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example              # Environment variables template
│   └── README.md                 # Backend documentation
│
├── public/                       # Static assets
├── Claude.md                     # This file
├── README.md                     # Project documentation
├── package.json                  # Node dependencies
├── tsconfig.json                 # TypeScript config
├── next.config.ts                # Next.js config
├── tailwind.config.ts            # Tailwind config
└── .gitignore                    # Git ignore rules
```

---

## Data Model

### Application Data Structure

```typescript
interface ApplicationData {
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
  countryIncomeSources?: string[];

  // System fields (added during resolution)
  justifications?: {
    [field: string]: string;  // field -> explanation
  };
  correctedFields?: {
    [field: string]: string;  // field -> old_value -> new_value
  };
}
```

### Red Flag Structure

```typescript
interface RedFlag {
  rule: string;           // Rule identifier (e.g., "company_exists")
  message: string;        // Human-readable issue description
  severity?: "low" | "medium" | "high";
  affectedFields: string[];  // Fields involved in the flag
}
```

---

## Component Details

### 1. Mock Form (Frontend)

**Purpose**: Collect applicant data for testing the validation system.

**Features**:
- All fields optional (for flexible testing)
- Clean, accessible form UI
- Client-side form state management
- Submit to backend `/validate` endpoint

**Key Files**:
- [components/MockForm.tsx](components/MockForm.tsx) - Form component
- [app/page.tsx](app/page.tsx) - Form page
- [lib/api.ts](lib/api.ts) - API client

**Form Sections**:

#### A. Personal Info
- Current Address (text)

#### B. Job Section
- Occupation (text)
- Job Title (text)
- Company Name (text)
- Company Address (text)

#### C. Income Section
- Monthly Income (number)
- Source of Income (text)
- Current Assets (number)
- Country Income Sources (text)

**Submit Flow**:
```
User fills form → Click Submit → POST to /api/validate
                                ↓
                         Backend validates
                                ↓
                         Returns red_flags[]
                                ↓
                  If flags exist → Show Chat Interface
```

---

### 2. Rule Engine (Backend)

**Purpose**: Analyze application data and identify potential red flags.

**Location**: [backend/app/services/rule_engine.py](backend/app/services/rule_engine.py)

#### Core Rules

##### Rule 1: Company Existence Check
```python
def check_company_exists(company_name: str) -> RedFlag | None:
    """
    Validate if company name appears legitimate.

    Red flags:
    - Too generic (e.g., "Company", "Inc", "Business")
    - Misspellings of known companies
    - Suspicious patterns (e.g., random characters)
    """
```

##### Rule 2: Address Distance Check
```python
def check_address_distance(home_address: str, work_address: str) -> RedFlag | None:
    """
    Compare home and work addresses.

    Red flags:
    - Extremely far distances (e.g., different countries)
    - Contradictory locations
    """
```

##### Rule 3: Income Plausibility
```python
def check_income_plausibility(
    occupation: str,
    monthly_income: float
) -> RedFlag | None:
    """
    Check if income aligns with occupation.

    Red flags:
    - Student with $50k/month income
    - Unusually high income for job title
    """
```

##### Rule 4: Field Contradictions
```python
def check_contradictions(data: ApplicationData) -> list[RedFlag]:
    """
    Detect logical inconsistencies.

    Examples:
    - Student + high salary + unrelated job
    - Income source doesn't match occupation
    """
```

#### Rule Engine Output

```python
{
    "red_flags": [
        {
            "rule": "company_exists",
            "message": "Company 'XYZ Corp' could not be verified",
        },
        {
            "rule": "distance_check",
            "message": "Home and work addresses are 500km apart",
        }
    ]
}
```

---

### 3. Interactive Chatbot (Backend)

**Purpose**: Resolve red flags through conversational AI.

**Location**: [backend/app/services/chatbot.py](backend/app/services/chatbot.py)

#### Behavior

The chatbot processes red flags **sequentially**:

```python
async def resolve_red_flags(
    application_data: ApplicationData,
    red_flags: list[RedFlag]
) -> tuple[ApplicationData, list[Message]]:
    """
    Process each red flag one by one.

    For each flag:
    1. Generate follow-up question
    2. Wait for user response
    3. Interpret response using GPT-4
    4. Update application data OR add justification
    5. Move to next flag

    Returns:
    - Updated application data
    - Conversation history
    """
```

#### GPT-4 Prompting Strategy

##### System Prompt
```
You are a helpful assistant reviewing an application form.
Your job is to resolve red flags by asking clarifying questions.

When the user responds:
1. Determine if it's a typo/correction → update the field
2. Determine if it's a reasonable explanation → add justification
3. If unclear → ask follow-up question

Output format:
{
  "action": "update" | "justify" | "ask_more",
  "field": "companyName",
  "value": "corrected value" | null,
  "justification": "explanation text" | null,
  "follow_up": "next question" | null
}
```

##### Example Conversations

**Example 1: Typo Correction**
```
Bot: I couldn't verify your company "SCB Bankk". Could you confirm the name?
User: Oh sorry, it's "SCB Bank" with one 'k'
Bot: Got it! I've updated your company name to "SCB Bank".

→ Action: Update companyName field
```

**Example 2: Reasonable Exception**
```
Bot: Your home is in Chiang Mai but your company is in Bangkok (700km apart). Can you explain?
User: I work fully remote from home
Bot: Thanks for clarifying! I've noted that you work remotely.

→ Action: Add justification to companyAddress field
```

**Example 3: Additional Questions**
```
Bot: You listed your occupation as "Student" but have a monthly income of $30,000. Can you explain?
User: I run an online business
Bot: What type of online business do you run?
User: E-commerce store selling electronics
Bot: Thanks! I've updated your income source to "E-commerce business owner".

→ Action: Update incomeSource field
```

---

## API Endpoints

### Backend (FastAPI)

#### `POST /api/validate`

**Purpose**: Validate application data and identify red flags.

**Request**:
```json
{
  "currentAddress": "123 Main St, Chiang Mai",
  "occupation": "Software Engineer",
  "jobTitle": "Senior Developer",
  "companyName": "Tech Corpz",
  "companyAddress": "456 Office Rd, Bangkok",
  "monthlyIncome": 80000,
  "incomeSource": "Employment",
  "currentAssets": 500000,
  "countryIncomeSources": ["Thailand"]
}
```

**Response**:
```json
{
  "red_flags": [
    {
      "rule": "company_exists",
      "message": "Company name 'Tech Corpz' could not be verified",
      "severity": "high",
      "affectedFields": ["companyName"]
    }
  ]
}
```

#### `POST /api/chat/resolve`

**Purpose**: Start chatbot resolution for red flags.

**Request**:
```json
{
  "applicationData": { /* full application data */ },
  "redFlags": [ /* array of red flags */ ]
}
```

**Response** (streaming):
```json
{
  "messages": [
    {
      "role": "assistant",
      "content": "I couldn't verify your company 'Tech Corpz'. Could you confirm the name?"
    }
  ],
  "status": "awaiting_response"
}
```

#### `POST /api/chat/message`

**Purpose**: Send user message during resolution.

**Request**:
```json
{
  "sessionId": "abc123",
  "message": "It's actually Tech Corps with an 's'"
}
```

**Response**:
```json
{
  "updatedData": { /* updated application data */ },
  "messages": [ /* conversation history */ ],
  "status": "resolved" | "awaiting_response",
  "remainingFlags": 2
}
```

---

## Implementation Phases

### Phase 1: MVP (Current)

#### ✅ Completed Features
- ✅ Folder structure (Next.js + FastAPI)
- ✅ Mock form UI with all fields (Next.js + TypeScript + Tailwind)
  - Personal Information section (current address)
  - Employment Information section (occupation, job title, company details)
  - Income Information section (monthly income, income source, assets, countries)
- ✅ Form submission and validation flow
- ✅ Basic rule engine with distance check rule
  - Google Geocoding API integration for address validation
  - Geodesic distance calculation (150km threshold)
  - Debug information display with lat/lng coordinates
- ✅ Traffic light validation UI (grey=pending, green=pass, red=fail)
- ✅ Debug info boxes showing geocoded addresses and distances
- ✅ Backend API structure with FastAPI
  - `/api/validate` endpoint working
  - Async rule engine service
  - CORS configured for local development
- ✅ Environment setup
  - Google Maps API key integrated
  - Backend and frontend servers running (ports 8000 and 3000)
  - Vercel deployment configuration

#### ✅ Interactive Chatbot (COMPLETED)
**Status**: OpenAI GPT-4o chatbot fully implemented with tool calling support

**Completed Features**:
- ✅ ChatBot modal component with conversation UI
- ✅ Chat service with OpenAI GPT-4o integration
- ✅ `/api/chat/message` endpoint for message handling
- ✅ Type definitions for chat interfaces
- ✅ "Fix It" button integration in MockForm
- ✅ Context-aware system prompts for each rule type
- ✅ Tool Registry Pattern for extensible function calling
- ✅ Employer Verification Tool integration
  - Calls existing EmployerVerificationService
  - Provides real-time company verification during chat
  - Supports company_name, company_website, and additional_context parameters
  - Shows verification sources (Google Sheets Allowlist + Perplexity AI)
- ✅ Pre-screening chat for political exposure questions

**Tool Registry Architecture**:
- **ToolHandler** base class for all tool implementations
- **ToolRegistry** centralized tool management
- **EmployerVerificationToolHandler** - First tool implementation
- Rule-specific tool mapping in ChatService
- Graceful error handling for tool execution
- Formatted tool results for LLM consumption

#### ✅ Validation Rules Implemented
**Current Order** (as displayed in UI):
1. **Blacklist Name Check** - Checks against restricted names list
2. **Employer Verification** - Multi-source company legitimacy check:
   - Google Sheets allowlist (cached, 1-hour TTL)
   - Perplexity AI web search with structured JSON output
   - Thailand business constraints (requires Thailand connection)
   - Securities industry exclusion (regulatory requirement)
3. **Address Distance Check** - Geodesic distance calculation between home and work (150km threshold)
4. **Political Exposure Check** - Pre-screening questionnaire with AI explanation validation

**Employer Verification Details**:
- Dual-source verification (ANY pass = PASS)
- Perplexity AI with Thailand-specific constraints:
  - Companies outside Thailand must have possibility of presence in Thailand
  - Securities/brokerage companies excluded (regulatory requirement)
  - Checks Thailand DBD, DataForThai, SET/SEC registries
  - Validates against international directories (Bloomberg, Reuters, Crunchbase)
- Debug information includes perplexity_details in red flag
- Chatbot receives initial verification context to guide questions

#### 🔄 Current Focus
- Testing complete flow with real-world scenarios
- Refining chatbot prompts based on user interactions
- Performance optimization for tool calls

### Phase 2: Enhanced Rules
- ⬜ External API for company verification
- ⬜ Address geocoding for distance calculation
- ⬜ Income benchmarking data
- ⬜ More sophisticated contradiction detection

### Phase 3: Production Ready
- ⬜ Database integration (PostgreSQL)
- ⬜ User authentication
- ⬜ Session management
- ⬜ Audit logging
- ⬜ Admin dashboard

### Phase 4: Advanced Features
- ⬜ Multi-language support
- ⬜ Document upload (ID, proof of income)
- ⬜ AI document verification
- ⬜ Risk scoring system

---

## Development Setup

### Prerequisites
- Node.js 20+
- Python 3.11+
- npm or yarn
- OpenAI API key

### Frontend Setup

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Open http://localhost:3000
```

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run server
uvicorn app.main:app --reload --port 8000

# Open http://localhost:8000/docs (Swagger UI)
```

---

## Environment Variables

### Frontend (`.env.local`)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend (`.env`)
```bash
# Google Maps API
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# OpenAI Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=2000

# Employer Verification Configuration
PERPLEXITY_API_KEY=pplx-...
EMPLOYER_ALLOWLIST_SHEET_URL=https://docs.google.com/spreadsheets/d/your_sheet_id/export?format=csv

# Server Configuration
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000
```

---

## Testing Strategy

### Frontend Testing
- Component tests (Jest + React Testing Library)
- E2E tests (Playwright)

### Backend Testing
- Unit tests (pytest)
- Integration tests (TestClient)
- LLM testing (mock OpenAI responses)

```bash
# Backend tests
cd backend
pytest

# Frontend tests
npm test

# E2E tests
npm run test:e2e
```

---

## Deployment

### Frontend (Vercel)
```bash
# Push to GitHub
git push origin main

# Auto-deploys via Vercel GitHub integration
# Or manual: vercel --prod
```

### Backend (Railway/Render)
```bash
# Railway
railway login
railway init
railway up

# Render
# Connect GitHub repo via Render dashboard
```

---

## Key Design Decisions

### Why Sequential Red Flag Resolution?
- **User Experience**: One question at a time is less overwhelming
- **Context**: Each answer can inform subsequent questions
- **Clarity**: User knows exactly what needs to be resolved

### Why FastAPI?
- **Performance**: Async support for LLM streaming
- **Type Safety**: Pydantic validation
- **Documentation**: Auto-generated OpenAPI docs
- **Python Ecosystem**: Easy integration with AI/ML libraries

### Why OpenAI GPT-4?
- **Instruction Following**: Excellent at structured output
- **Context Understanding**: Can interpret ambiguous responses
- **Reliability**: Consistent quality for business logic

### Why No Database (Phase 1)?
- **Simplicity**: Focus on core validation logic
- **Speed**: Faster development iteration
- **Testing**: Easier to test with in-memory data

---

## Future Enhancements

### Short Term
- Add more validation rules
- Improve GPT-4 prompts for better accuracy
- Add conversation memory/context

### Medium Term
- Database persistence
- Multi-step forms with progress saving
- Admin review dashboard

### Long Term
- Real-time collaboration (multiple reviewers)
- ML-based anomaly detection
- Integration with credit bureaus/databases

---

## Security Considerations

### Phase 1
- No sensitive data storage (in-memory only)
- HTTPS in production
- API key protection (environment variables)
- CORS configuration

### Future Phases
- Data encryption at rest
- PII detection and masking
- Access control (RBAC)
- Audit logging
- GDPR compliance

---

## Performance Targets

### Frontend
- Page load: < 2s
- Form submission: < 500ms
- Chat response: < 3s (streaming)

### Backend
- Rule engine: < 100ms
- GPT-4 first token: < 1s
- Full resolution: < 30s per flag

---

## Troubleshooting

### Common Issues

**Issue**: Form submission fails
- Check NEXT_PUBLIC_API_URL in `.env.local`
- Verify backend is running on port 8000

**Issue**: GPT-4 responses are slow
- Use `gpt-4.1-mini` for faster responses
- Implement streaming for better UX

**Issue**: Rule engine false positives
- Adjust rule thresholds in rule_engine.py
- Add more context to rules

---

## Contributing

### Code Style
- Frontend: ESLint + Prettier
- Backend: Black + isort + flake8

### Commit Convention
```
feat: add company verification rule
fix: resolve chatbot memory leak
docs: update API documentation
test: add rule engine tests
```

---

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAI API Reference](https://platform.openai.com/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)

---

## Contact & Support

For questions or issues, please open a GitHub issue or contact the development team.

---

**Last Updated**: 2025-12-11
**Version**: 0.2.0 (MVP Phase - Chatbot with Tool Calling Completed)
