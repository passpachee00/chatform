"use client";

import { useState, useEffect, useRef } from "react";
import { PreScreeningData, ChatMessage } from "@/types";

interface PreScreeningSectionProps {
  data: PreScreeningData;
  onResponseChange: (response: "yes" | "no") => void;
  onChatComplete: (explanation: string, chatHistory: ChatMessage[]) => void;
}

export function PreScreeningSection({
  data,
  onResponseChange,
  onChatComplete,
}: PreScreeningSectionProps) {
  const [showChat, setShowChat] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>(data.chatHistory);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Initialize chat when user clicks Yes
  const handleYesClick = () => {
    setShowChat(true);
    if (messages.length === 0) {
      setMessages([
        {
          role: "assistant",
          content:
            "Thank you for indicating you fall into one of these categories. Could you please explain your situation in more detail? For example, if you're a US citizen or if you or a relative holds a political position, please provide specifics.",
          timestamp: new Date(),
        },
      ]);
    }
  };

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return;

    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    const userMessage: ChatMessage = {
      role: "user",
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/prescreening/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: inputValue,
          conversationHistory: messages,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to send message");
      }

      const responseData = await response.json();

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: responseData.content,
        timestamp: new Date(responseData.timestamp),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Auto-save conversation after each message
      const updatedMessages = [...messages, userMessage, assistantMessage];
      const userMessagesText = updatedMessages
        .filter((m) => m.role === "user")
        .map((m) => m.content)
        .join(" ");
      onChatComplete(userMessagesText, updatedMessages);
    } catch (error) {
      console.error("Chat error:", error);
      const errorMessage: ChatMessage = {
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">
        Pre-Screening Questions
      </h3>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <p className="text-gray-800 mb-4">Are you any of the below:</p>
        <ul className="list-disc list-inside mb-4 text-gray-700">
          <li>US citizen</li>
          <li>
            You or your close relative holding any political position (e.g.,
            Minister, Governor)
          </li>
        </ul>

        {/* Yes/No Buttons */}
        {!showChat && (
          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => onResponseChange("no")}
              className={`px-6 py-2 rounded-lg ${
                data.response === "no"
                  ? "bg-green-600 text-white"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
            >
              No
            </button>

            <button
              type="button"
              onClick={handleYesClick}
              className="px-6 py-2 rounded-lg bg-gray-200 text-gray-700 hover:bg-gray-300"
            >
              Yes (Please explain)
            </button>
          </div>
        )}

        {/* Inline Chat Interface */}
        {showChat && (
          <div className="space-y-4">
            {/* Messages */}
            <div className="max-h-64 overflow-y-auto space-y-3 bg-white rounded-lg p-4 border border-blue-300">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${
                    msg.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[80%] px-3 py-2 rounded-lg text-sm ${
                      msg.role === "user"
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 text-black"
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 text-black px-3 py-2 rounded-lg text-sm">
                    <div className="flex gap-1">
                      <span className="animate-bounce">●</span>
                      <span className="animate-bounce delay-100">●</span>
                      <span className="animate-bounce delay-200">●</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="flex gap-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your response..."
                className="flex-1 px-3 py-2 border-2 border-gray-400 bg-white rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-blue-600 text-black text-sm shadow-sm"
                disabled={isLoading}
              />
              <button
                type="button"
                onClick={handleSend}
                disabled={isLoading || !inputValue.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm"
              >
                Send
              </button>
            </div>
          </div>
        )}

        {/* Show status if answered */}
        {!showChat && data.answered && data.response === "no" && (
          <p className="mt-4 text-green-700 text-sm">✓ Response recorded</p>
        )}

        {!showChat && data.answered && data.response === "yes" && data.explanation && (
          <p className="mt-4 text-blue-700 text-sm">
            ✓ Explanation provided ({data.chatHistory.length} messages)
          </p>
        )}
      </div>
    </div>
  );
}
