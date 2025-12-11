"""
Chat service for handling OpenAI GPT-4o conversations to resolve validation red flags
"""

import os
from typing import List, Dict, Any
from openai import AsyncOpenAI
from app.schemas.application import ApplicationData, RedFlag, ChatMessage
from app.services.tools import ToolRegistry, EmployerVerificationToolHandler


class ChatService:
    """Service for managing AI-powered chat conversations"""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))

        # Initialize tool registry
        self.tool_registry = ToolRegistry()

        # Register tools
        self.tool_registry.register(EmployerVerificationToolHandler())

    def build_system_prompt(
        self, red_flag: RedFlag, app_data: ApplicationData
    ) -> str:
        """
        Generate context-aware system prompt for the AI assistant

        Args:
            red_flag: The validation red flag to resolve
            app_data: The application data for context

        Returns:
            System prompt string
        """
        affected_fields_text = ", ".join(red_flag.affectedFields)

        # Build context from application data (conditionally based on rule type)
        context_parts = []

        # For blacklist_check, provide minimal/no context
        # The user just needs to defend/explain, not provide additional data
        if red_flag.rule != "blacklist_check":
            if app_data.currentAddress:
                context_parts.append(f"Current Address: {app_data.currentAddress}")
            if app_data.companyAddress:
                context_parts.append(f"Company Address: {app_data.companyAddress}")
            if app_data.employmentType:
                context_parts.append(f"Employment Type: {app_data.employmentType}")
            if app_data.jobTitle:
                context_parts.append(f"Job Title: {app_data.jobTitle}")
            if app_data.companyName:
                context_parts.append(f"Company Name: {app_data.companyName}")
            if app_data.monthlyIncome:
                context_parts.append(f"Monthly Income: ${app_data.monthlyIncome:,.2f}")
            if app_data.sourceOfFunds:
                context_parts.append(f"Source of Funds: {app_data.sourceOfFunds}")
            if app_data.currentAssets:
                context_parts.append(f"Current Assets: ${app_data.currentAssets:,.2f}")
            if app_data.countryIncomeSources:
                context_parts.append(
                    f"Country Income Sources: {app_data.countryIncomeSources}"
                )

        context = "\n".join(context_parts) if context_parts else "(No additional context provided)"

        system_prompt = f"""You are a helpful assistant helping the customer provide the right information to open their account.
To proceed, we must clear all validation red flags, as required by company policy and regulations.

**Your Role:**
- Help the user resolve the validation issue.
- Ask clarifying questions to understand the situation.
- Give the customer a chance to explain, justify, or correct their data.
- Be friendly, professional, and concise.
- 

**Validation Issue Details:**
- Rule: {red_flag.rule}
- Message: {red_flag.message}
- Affected Fields: {affected_fields_text}

**Application Context:**
{context}

**Instructions:**
1. If this is the first message (conversation history is empty), explain the issue, and ask the customer to explain the situation.
2. Don't over share how we make the decision . The goal is to seek the truth but at the same time prevent fraud.
2. Listen carefully to the customer's explanation or correction.
3. Ask follow-up questions only if needed to fully understand the situation.
4. Provide clear and simple guidance on what the customer should do next.
5. Be empathetic and understanding — there are many legitimate reasons behind unusual data.
6. Once the customer provides a reasonable explanation or correction, acknowledge it positively and end the conversation.

**Important:**
- Do not make up information.
- Do not assume the user is lying or committing fraud.
- Focus on helping them provide accurate information or valid explanations.
- If they give a reasonable explanation, accept it as valid unless the red flag explicitly requires more detail."""

        # Add rule-specific guidance (conditionally based on rule type)
        if red_flag.rule == "blacklist_check":
            system_prompt += """

**Rule-Specific Guidance for Blacklist Check:**
IMPORTANT: For the FIRST message, you MUST directly address the blacklist issue. Say something like:
"I see that your name appears in our restricted list. This doesn't necessarily mean there's an issue - it could be a name coincidence or administrative error. Can you help me understand why your name might be on this list?"

Key points:
- IMMEDIATELY ask them to explain why their name might be on the restricted list
- Don't be generic or vague - directly mention the restricted list
- Common legitimate reasons include:
  * Name similarity/coincidence (same name as someone else)
  * Previous identity verification issues that were resolved
  * Administrative error that needs to be corrected
  * Changed legal name but old name remains in system
  * Family member with similar name
- Use common sense to evaluate their explanation
- If their explanation seems reasonable and credible, accept it
- Focus on understanding the situation, not interrogating them
- Be empathetic - being on a restricted list can be stressful"""

        elif red_flag.rule == "distance_check":
            # Extract Google geocoding status from debugInfo if available
            geocoding_context = ""
            if red_flag.debugInfo:
                current_addr_info = red_flag.debugInfo.get("currentAddress", {})
                company_addr_info = red_flag.debugInfo.get("companyAddress", {})

                current_status = current_addr_info.get("google_status")
                company_status = company_addr_info.get("google_status")

                # Build context message for geocoding failures
                if current_status and current_status != "OK":
                    geocoding_context += f"\n- Current Address: Google Maps returned '{current_status}' (address could not be validated)"

                if company_status and company_status != "OK":
                    geocoding_context += f"\n- Company Address: Google Maps returned '{company_status}' (address could not be validated)"

                if geocoding_context:
                    geocoding_context = f"\n**Geocoding Issues:**{geocoding_context}\n"

            system_prompt += f"""

**Rule-Specific Guidance for Distance Check:**
{geocoding_context}
- The issue may be about addresses being far apart OR addresses that couldn't be validated by Google Maps
- If Google Maps couldn't validate an address (ZERO_RESULTS, INVALID_REQUEST, etc.), ask the user to provide a complete, valid address
- For distance issues (when addresses are valid but far apart): Customers may work remotely, visit the office only a few days per week, travel for work, or have multiple residences
- Your job is to help clarify the situation, not to assume anything is wrong
- Accept reasonable explanations about their work-life situation"""

        elif red_flag.rule == "employer_verification_check":
            # Extract Perplexity explanation from debugInfo if available
            perplexity_context = ""
            if red_flag.debugInfo and "perplexity_details" in red_flag.debugInfo:
                perplexity_details = red_flag.debugInfo["perplexity_details"]
                explanation = perplexity_details.get("explanation", "")
                if explanation:
                    perplexity_context = f"""

**Initial Verification Context:**
Our AI verification system already attempted to verify '{app_data.companyName}' and reported:
"{explanation}"

This gives you context about what went wrong (e.g., typo, incomplete name, not found in public records, multiple similar companies found)."""

            system_prompt += f"""

**Rule-Specific Guidance for Employer Verification:**
IMPORTANT: You have access to a TOOL called `verify_employer` that can check if a company is legitimate.
{perplexity_context}

**When to use the tool:**
- When the user provides a CORRECTED company name (e.g., "It's actually SCB Bank, not SCB Bankk")
- When the user provides additional information like a company website (to re-verify with more context)

**How to help the user:**
1. FIRST MESSAGE: Explain the verification issue using the context above. Ask clarifying questions like:
   - "Could there be a typo in the company name?"
   - "Do you have the full official company name?"
   - "Do you have a company website or registration details?"
2. When user provides a CORRECTED name or website → Use the verify_employer tool to verify it
3. If verification PASSED:
   - Congratulate them
   - Check which source verified the company:
     * If Google Sheets Allowlist passed → Simply say "Your company was verified through our pre-approved company list" (no need to mention Perplexity details)
     * If Perplexity AI passed → Explain the Perplexity verification details, mention the official company name found
   - End the conversation positively
4. If verification FAILED again:
   - Explain the result
   - Try to gather more information (website, full official name, location)
   - If user provides additional info, use the tool again with that context

**Important Notes:**
- Be transparent about what you're checking
- Explain that verification checks public business registries and web sources
- Use the initial Perplexity explanation to guide your questions intelligently:
  * If it says "multiple similar names found" → ask for exact official name
  * If it mentions a typo → ask them to provide the correct spelling
  * If it says "not found" → ask if they have a website or registration details
- If user gives reasonable explanation but tool still fails after multiple attempts, document their explanation
- Multiple attempts with corrected information are encouraged"""

        elif red_flag.rule == "source_of_funds_alignment_check":
            # Build alignment matrix table for AI reference
            from app.services.rule_engine import SOURCE_OF_FUNDS_ALIGNMENT

            alignment_matrix = "\n".join([
                f"  - {emp_type}: {', '.join(sources)}"
                for emp_type, sources in SOURCE_OF_FUNDS_ALIGNMENT.items()
            ])

            system_prompt += f"""

**Rule-Specific Guidance for Source of Funds Alignment:**

**Context - What Triggered This Flag:**
- Employment Type: {app_data.employmentType or "(not provided)"}
- Source of Funds: {app_data.sourceOfFunds or "(not provided)"}

**Alignment Matrix (Reference):**
{alignment_matrix}

**Your Goal:**
Match these two variables: Employment Type ↔ Source of Funds

**Your Approach:**
1. Mention both employment type and source of funds as the cause
2. Ask for clarification on employment type, source of funds, or both
3. Use common sense to determine if explanation is legitimate
4. Help classify ambiguous employment types (e.g., "Freelance golf caddie" → ask clarifying questions to determine if Freelancer or Self-Employed)

**CRITICAL - Before Approving (PASS):**
Before you decide to PASS, you MUST:

1. **Verify the alignment matrix**: Check if this exact combination exists in the matrix above
2. **If combination NOT in matrix**, reason about WHY it's restricted:
   - What's the intent behind the restriction?
   - Does the user's situation truly fit their chosen employment type, or should they reclassify?
3. **Decide**:
   - If user clearly fits a different employment type → Help them reclassify
   - If it's a genuine edge case with solid justification → PASS
   - If justification is weak or vague → FLAG

**Decision Making:**
- DEFAULT: Follow the alignment matrix
- PASS if: (a) Combination exists in matrix, OR (b) Genuine edge case with solid justification
- If combination not in matrix but user clearly fits a different employment type → Help them reclassify
"""

        return system_prompt

    async def send_message(
        self,
        user_message: str,
        red_flag: RedFlag,
        app_data: ApplicationData,
        conversation_history: List[ChatMessage],
    ) -> str:
        """
        Send message to OpenAI and get response

        Args:
            user_message: The user's message (empty string for initialization)
            red_flag: The red flag being discussed
            app_data: Application data for context
            conversation_history: Previous conversation messages

        Returns:
            Assistant's response content

        Raises:
            Exception: If API call fails
        """
        try:
            # Build system prompt
            system_prompt = self.build_system_prompt(red_flag, app_data)

            # Format messages for OpenAI API
            messages = [{"role": "system", "content": system_prompt}]

            # Add conversation history
            for msg in conversation_history:
                messages.append({"role": msg.role, "content": msg.content})

            # Add user message if not initialization
            if user_message:
                messages.append({"role": "user", "content": user_message})

            # Determine which tools to provide based on red flag
            tool_names = self._get_tools_for_rule(red_flag.rule)
            tools = None
            if tool_names:
                tools = self.tool_registry.get_schemas(tool_names)

            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=0.5,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            # Handle response (may include tool calls)
            return await self._handle_response(response, messages, red_flag, app_data)

        except Exception as e:
            # Log error (in production, use proper logging)
            print(f"Error calling OpenAI API: {e}")
            raise Exception(f"Failed to get AI response: {str(e)}")

    def _get_tools_for_rule(self, rule: str) -> List[str]:
        """
        Determine which tools should be available for a given rule

        Args:
            rule: Red flag rule name

        Returns:
            List of tool names to make available
        """
        tool_map = {
            "employer_verification_check": ["verify_employer"],
            # Future mappings:
            # "distance_check": ["geocode_address", "calculate_distance"],
            # "income_plausibility": ["check_income_benchmark"],
        }

        return tool_map.get(rule, [])

    async def _handle_response(
        self,
        response: Any,
        messages: List[Dict[str, Any]],
        red_flag: RedFlag,
        app_data: ApplicationData
    ) -> str:
        """Handle response, executing tools if needed"""
        assistant_message = response.choices[0].message

        # If no tool calls, return content directly
        if not assistant_message.tool_calls:
            return assistant_message.content or ""

        # Add assistant message with tool calls to history
        messages.append({
            "role": "assistant",
            "content": assistant_message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in assistant_message.tool_calls
            ]
        })

        # Execute each tool call
        for tool_call in assistant_message.tool_calls:
            try:
                # Parse arguments
                import json
                args = json.loads(tool_call.function.arguments)

                # Build context for tool execution
                context = {
                    "red_flag": red_flag,
                    "app_data": app_data
                }

                # Execute tool via registry
                tool_result = await self.tool_registry.execute(
                    tool_name=tool_call.function.name,
                    arguments=args,
                    context=context
                )

                # Add tool response to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": tool_result
                })

            except Exception as e:
                # Handle tool execution errors gracefully
                error_message = f"Error executing tool '{tool_call.function.name}': {str(e)}"
                print(f"Tool execution error: {error_message}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": f"❌ Tool execution failed: {str(e)}"
                })

        # Get final response after tool execution
        final_response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=0.5
        )

        return final_response.choices[0].message.content or ""

    async def get_completion(self, messages: List[Dict[str, str]]) -> str:
        """
        Generic method to get completion from OpenAI

        Args:
            messages: List of message dicts with role/content
                     (should include system prompt if needed)

        Returns:
            Assistant's response content

        Raises:
            Exception: If API call fails
        """
        try:
            # Call OpenAI API with provided messages
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=0.5,
            )

            # Extract response content
            assistant_message = response.choices[0].message.content

            if not assistant_message:
                raise ValueError("Empty response from OpenAI")

            return assistant_message

        except Exception as e:
            # Log error (in production, use proper logging)
            print(f"Error calling OpenAI API: {e}")
            raise Exception(f"Failed to get AI response: {str(e)}")
