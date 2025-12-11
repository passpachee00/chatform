# ChatForm Platform Architecture - Integration Guide

> **Audience**: Product Managers, Engineering Managers, Customer Stakeholders
> **Purpose**: Technical discussion guide for iOS integration

---

## Executive Summary

**Problem**: Customers currently rely on manual call centers to fix application errors
**Solution**: ChatForm provides real-time AI-powered error resolution during form submission
**Integration Time**: 5-6 days total (1 day for customer's iOS team)

---

## Current vs. Desired Flow

### Today (Manual Process)
```
User fills form → Submits → Call center receives
                            ↓
                    Errors detected
                            ↓
                    User must CALL in
                            ↓
                    Agent fixes manually
                            ↓
                    User resubmits
```
**Problems**: Slow, expensive, poor user experience

### With ChatForm (Automated)
```
User fills form → Submits → ChatForm validates in real-time
                            ↓
                    Errors detected
                            ↓
                    AI chatbot opens (in-app)
                            ↓
                    User fixes via conversation
                            ↓
                    Clean data → Submission continues
```
**Benefits**: Instant resolution, no phone calls, better conversion

---

## Integration Approach: Managed SDK

We provide a **pre-built SDK wrapper** that handles all complexity. Customer's iOS team writes **~5 lines of code**.

### Why SDK vs. Raw API?

| Approach | Customer's Work | Business Logic Owner | Change Management |
|----------|----------------|---------------------|-------------------|
| Raw API (Manual) | ~30 lines of code | Customer's app | App Store update required |
| **Managed SDK** ✅ | **~5 lines of code** | **ChatForm SDK** | **Update SDK only (no app release)** |

**Decision**: SDK approach minimizes customer's engineering effort and gives us control over business logic.

---

## How It Works (Customer's Perspective)

### Step 1: Receive SDK File
We provide: `ChatFormSDK.swift` (or `.ts` for React Native, `.dart` for Flutter)

### Step 2: One-Time Setup
```swift
// In app initialization
ChatFormSDK.configure(apiKey: "provided_by_chatform")
```

### Step 3: Validate on Submit
```swift
// When user taps "Submit"
ChatFormSDK.shared.validate(formData) { result in
    switch result {
    case .success(let cleanData):
        // ✅ Submit to customer's backend
        submitToOurBackend(cleanData)
    case .failure(let error):
        // ❌ Show error message
        showError(error)
    }
}
```

**That's all the customer needs to write.**

---

## What Happens Under the Hood

The SDK we provide handles:

1. **API Call**: Posts form data to ChatForm backend
2. **Decision Logic**: Determines if chat intervention is needed
3. **WebView Management**: Opens chat interface (if errors exist)
4. **User Resolution**: User fixes errors via AI conversation
5. **Callback**: Returns clean data to iOS app

**Customer never sees this complexity** - it's all handled by our SDK.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────┐
│           Customer's iOS App                     │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  FormViewController                        │ │
│  │  func submitForm() {                       │ │
│  │    ChatFormSDK.validate(data) { result in  │ │  ← Customer writes this
│  │      // Handle result                      │ │
│  │    }                                       │ │
│  │  }                                         │ │
│  └─────────────────┬──────────────────────────┘ │
│                    │                            │
│  ┌─────────────────▼──────────────────────────┐ │
│  │  ChatFormSDK.swift (We provide)           │ │  ← We write this
│  │  • Calls validation API                   │ │
│  │  • Opens WebView if needed                │ │
│  │  • Handles chat completion                │ │
│  └─────────────────┬──────────────────────────┘ │
└────────────────────┼───────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────┐        ┌──────────────────┐
│   ChatForm   │        │  ChatForm WebView│
│   Backend    │◄───────┤  (Chat Interface)│
│   (API)      │        │  (In-App Browser)│
└──────────────┘        └──────────────────┘
```

---

## Responsibilities Matrix

### ChatForm Delivers
| Component | Description | Timeline |
|-----------|-------------|----------|
| **SDK File** | `ChatFormSDK.swift` / `.ts` / `.dart` | Day 4 |
| **Backend API** | Validation + chat endpoints (5 endpoints) | Day 1-3 |
| **WebView Page** | Mobile-optimized chat interface | Day 3 |
| **API Key** | Authentication credentials | Day 5 |
| **Documentation** | Integration guide + API reference | Day 4-5 |

### Customer Delivers
| Component | Description | Timeline |
|-----------|-------------|----------|
| **Integration Code** | ~5 lines calling SDK | Day 6 |
| **Error Handling** | Display error if network fails | Day 6 |
| **Testing** | Test with sample data | Day 6-7 |

---

## Integration Timeline

```
Day 1:   ChatForm: Database setup (PostgreSQL)
Day 2-3: ChatForm: Build backend API (validation + chat)
Day 3:   ChatForm: Build WebView resolution page
Day 4:   ChatForm: Build SDK wrapper (Swift/React Native/Flutter)
Day 4-5: ChatForm: Documentation + API key generation
------------------------------------------------------------
Day 6:   Customer: Integrate SDK (~1 day of work)
Day 6-7: Joint: End-to-end testing
------------------------------------------------------------
Day 7:   Launch ✅
```

**Total: 5-6 days** from kickoff to production

---

## Implementation Overview

To make this work, we need to build 3 core components:

### 1. Backend Persistence
**Current state**: The backend validates data but doesn't save anything (stateless)
**What we need**: Save each application to a database with a unique session ID

**Why**: When the iOS app opens the WebView for chat resolution, the WebView needs to load the application data using that session ID.

### 2. Mobile Resolution Page
**What we need**: Create a mobile-optimized chat page at `/resolve/[session_id]`
**Purpose**: This is the page that opens inside the iOS WebView when errors are found

**Key feature**: When the user finishes fixing errors, this page sends a message back to the iOS app using `postMessage` bridge, allowing the app to close the WebView and continue submission.

### 3. SDK Wrapper
**What we need**: Build `ChatFormSDK.swift` (or `.ts`/`.dart` depending on customer's stack)
**Purpose**: The SDK handles all the complexity - API calls, WebView management, callbacks

**Customer integration**: Just 5 lines of code calling `ChatFormSDK.validate()`

**Bottom line**: Customer's iOS team only sees steps 1-3 in "How It Works" above. We handle all the complexity inside components 1-3.

---

## Technical Requirements

### Before We Start

**Critical Question**: What is the iOS app built with?

| Platform | SDK We'll Provide | Package Format |
|----------|-------------------|----------------|
| Native iOS (Swift/SwiftUI) | `ChatFormSDK.swift` | Single file |
| React Native | `@chatform/react-native-sdk` | npm package |
| Flutter | `chatform_flutter` | pub package |
| Kotlin Multiplatform | `ChatFormSDK.kt` | Single file |

**👉 Action**: Ask customer's engineering team which platform they use.

### Customer's Environment Needs
- iOS 13+ (for WKWebView support)
- Internet connectivity (API calls)
- Keychain access (for API key storage)

---

## Discussion Questions for Customer

### Technical
1. **Platform**: Is the iOS app built with Swift, React Native, Flutter, or other?
2. **Staging**: Do you have a staging environment we can test against?
3. **Timeline**: When do you need this live?
4. **Error Handling**: What should happen if ChatForm API is temporarily down?

### Business
5. **User Volume**: How many form submissions per day?
6. **Data Sensitivity**: Any special compliance requirements (GDPR, HIPAA)?
7. **Branding**: Do you want the chat UI customized with your brand colors?
8. **SLA**: What's your expected uptime requirement?

---

## Key Benefits

### For End Users
- ✅ **No phone calls** - Fix errors instantly in-app
- ✅ **Faster resolution** - AI chat vs. waiting for call center
- ✅ **Better experience** - Conversational vs. confusing error messages

### For Customer (Business)
- ✅ **Lower costs** - Reduce call center volume
- ✅ **Higher conversion** - Fewer abandoned applications
- ✅ **Better data quality** - AI ensures clean submissions

### For Customer (Engineering)
- ✅ **Minimal integration** - 5 lines of code vs. building from scratch
- ✅ **Fast time-to-market** - 1 day of work vs. 2-3 weeks
- ✅ **Zero maintenance** - We handle updates, no app releases needed

---

## Security & Privacy

### Data Handling
- **Encryption**: All API calls use HTTPS (TLS 1.3)
- **Storage**: Application data stored for 30 days, then auto-deleted
- **Access**: API key authentication, scoped to customer's tenant
- **Compliance**: GDPR-compliant (data deletion on request)

### API Key Management
- Stored in iOS Keychain (secure storage)
- Hashed with bcrypt on backend
- Unique per customer
- Can be rotated without app update

---

## Success Metrics

### Phase 1 (Week 1-2)
- Integration complete
- 100% of submissions validated
- <3s average chat resolution time

### Phase 2 (Month 1)
- Measure call center volume reduction
- Track application completion rate
- Collect user satisfaction scores

### Phase 3 (Quarter 1)
- Calculate ROI (call center savings vs. ChatForm cost)
- Identify new validation rules based on data
- Expand to additional forms

---

## Pricing Model (To Be Discussed)

**Option A: Per Application**
- $0.10 per application validated
- $0.50 per application requiring chat resolution

**Option B: Monthly Subscription**
- $500/month for up to 5,000 applications
- $1,000/month for up to 20,000 applications

**Option C: Enterprise**
- Custom pricing based on volume
- Dedicated support
- Custom rule development

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| **ChatForm API down** | SDK gracefully degrades (allows submission without validation) |
| **Slow API response** | 30-second timeout, then fallback |
| **User closes WebView** | Data saved, can resume later or skip validation |
| **Integration complexity** | We provide reference implementation + 1:1 support |

---

## Next Steps

### Pre-Kickoff (This Week)
1. ✅ Customer confirms iOS platform (Swift/React Native/Flutter)
2. ✅ Customer provides staging environment details
3. ✅ Both parties sign technical SOW

### Week 1 (ChatForm Development)
1. Day 1: Database + API infrastructure
2. Day 2-3: Validation API + chat endpoints
3. Day 3: WebView resolution page
4. Day 4: SDK development
5. Day 5: Documentation + API key

### Week 2 (Integration & Testing)
1. Day 6: Customer integrates SDK
2. Day 6-7: Joint testing
3. Day 7: Production deployment

### Post-Launch
1. Week 2-4: Monitor metrics
2. Month 1: Iteration based on feedback
3. Quarter 1: ROI review

---

## Contact & Support

**ChatForm Team**:
- Project Lead: [Name]
- Technical Lead: [Name]
- Email: support@chatform.io
- Slack Channel: #customer-[company-name]

**Customer Team (Required)**:
- Engineering Manager: [To be assigned]
- iOS Lead Developer: [To be assigned]
- Product Manager: [To be assigned]

---

## Appendix: Technical Deep Dive

### API Endpoints (Overview)

**POST /api/v1/applications**
- Purpose: Validate application data
- Input: Form data + metadata
- Output: Validation status + resolution URL (if needed)

**GET /api/v1/applications/{id}**
- Purpose: Load application for WebView
- Input: Application ID + JWT token
- Output: Application data + red flags

**POST /api/v1/applications/{id}/chat**
- Purpose: Send chat message
- Input: User message
- Output: AI response

### Validation Rules (Current)
1. **Blacklist Check**: Name validation
2. **Employer Verification**: Company legitimacy (Perplexity AI + allowlist)
3. **Address Distance**: Home vs. work proximity (150km threshold)
4. **Political Exposure**: Pre-screening questionnaire

**Note**: Rules are configurable per customer (future enhancement).

---

## What Data Do We Return?

After validation (and resolution if needed), the customer's iOS app receives:

| Field | Description | Purpose |
|-------|-------------|---------|
| **Clean Data** | The validated/corrected form data | Ready to submit to customer's backend |
| **Changes** | List of fields that changed (before → after) | Transparency on what was modified |
| **Resolution Audit** | For each validation rule that failed | Compliance & audit trail |

### Resolution Audit Format

For compliance and audit purposes, each failed rule includes:

- **Rule**: Which validation failed (e.g., "employer_verification")
- **Explanation**: Why it failed (e.g., "Company 'SCB Bankk' could not be verified")
- **Fixed**: Was the issue resolved? (true/false)
- **How**: How it was fixed (e.g., "User corrected typo to 'SCB Bank'" or "User confirmed remote work arrangement")

**Example**:
```
Employer Verification Rule
├─ Failed: Company name 'SCB Bankk' could not be verified
├─ Fixed: Yes
└─ Resolution: User corrected company name to 'SCB Bank'
```

This provides complete transparency for regulatory compliance and internal auditing.

---

**Document Version**: 1.1
**Last Updated**: 2025-12-12
**Status**: Ready for customer discussion


--- 

Mock response 

"""{
  "applicationId": "app_xyz789",
  "status": "resolved",
  
  "data": {
    "companyName": "Google Thailand",
    "monthlyIncome": 200000,
    "currentAddress": "Chiang Mai",
    "companyAddress": "Bangkok"
  },
  
  "changes": [
    { "field": "companyName", "from": "Googel", "to": "Google Thailand" }
  ],
  
  "resolutions": [
    {
      "rule": "employer_verification",
      "explanation": "Company 'Googel' could not be verified",
      "fixed": true,
      "how": "User corrected spelling to 'Google Thailand'"
    },
    {
      "rule": "address_distance",
      "explanation": "Home and work are 700km apart",
      "fixed": true,
      "how": "User works fully remote"
    },
    {
      "rule": "income_plausibility",
      "explanation": "Income of 200,000 THB/month is high for occupation",
      "fixed": true,
      "how": "User confirmed senior position with stock compensation"
    }
  ]
}""" 