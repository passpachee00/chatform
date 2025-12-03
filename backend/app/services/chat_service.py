"""
Chat service for handling OpenAI GPT-4o conversations to resolve validation red flags
"""

import os
from typing import List, Dict, Any
from openai import AsyncOpenAI
from app.schemas.application import ApplicationData, RedFlag, ChatMessage


class ChatService:
    """Service for managing AI-powered chat conversations"""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))

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

        # Build context from application data
        context_parts = []

        if app_data.currentAddress:
            context_parts.append(f"Current Address: {app_data.currentAddress}")
        if app_data.companyAddress:
            context_parts.append(f"Company Address: {app_data.companyAddress}")
        if app_data.occupation:
            context_parts.append(f"Occupation: {app_data.occupation}")
        if app_data.jobTitle:
            context_parts.append(f"Job Title: {app_data.jobTitle}")
        if app_data.companyName:
            context_parts.append(f"Company Name: {app_data.companyName}")
        if app_data.monthlyIncome:
            context_parts.append(f"Monthly Income: ${app_data.monthlyIncome:,.2f}")
        if app_data.incomeSource:
            context_parts.append(f"Income Source: {app_data.incomeSource}")
        if app_data.currentAssets:
            context_parts.append(f"Current Assets: ${app_data.currentAssets:,.2f}")
        if app_data.countryIncomeSources:
            context_parts.append(
                f"Country Income Sources: {app_data.countryIncomeSources}"
            )

        context = "\n".join(context_parts)

        system_prompt = f"""You are a helpful assistant helping the customer provide the right information to open their account.
To proceed, we must clear all validation red flags, as required by company policy and regulations.

**Your Role:**
- Help the user resolve the validation issue.
- Ask clarifying questions to understand the situation.
- Give the customer a chance to explain, justify, or correct their data.
- Be friendly, professional, and concise.

**Validation Issue Details:**
- Rule: {red_flag.rule}
- Message: {red_flag.message}
- Affected Fields: {affected_fields_text}

**Application Context:**
{context}

**Instructions:**
1. If this is the first message (conversation history is empty), briefly introduce yourself, explain the issue, and ask the customer to explain the situation.
2. Listen carefully to the customer's explanation or correction.
3. Ask follow-up questions only if needed to fully understand the situation.
4. Provide clear and simple guidance on what the customer should do next.
5. Be empathetic and understanding — there are many legitimate reasons behind unusual data.
6. **Important Example:** If the issue is about home and work addresses being far apart, remember that this can be completely normal.
   Customers may work remotely, visit the office only a few days per week, travel for work, or have multiple residences.
   Your job is to help clarify the situation, not to assume anything is wrong.
7. Once the customer provides a reasonable explanation or correction, acknowledge it positively and move on to the next red flag if any. Otherwise, thank them for the clarification.

**Important:**
- Do not make up information.
- Do not assume the user is lying or committing fraud.
- Focus on helping them provide accurate information or valid explanations.
- If they give a reasonable explanation, accept it as valid unless the red flag explicitly requires more detail."""

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

            # Call OpenAI API
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
