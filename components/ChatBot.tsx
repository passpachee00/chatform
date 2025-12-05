"use client";

import { useState, useEffect, useRef } from "react";
import { useChat } from "@/hooks/useChat";
import type { RedFlag, ApplicationData, ChatMessage } from "@/types";

interface ChatBotProps {
  redFlag: RedFlag;
  applicationData: ApplicationData;
  isOpen: boolean;
  onClose: () => void;
}

export default function ChatBot({
  redFlag,
  applicationData,
  isOpen,
  onClose,
}: ChatBotProps) {
  const {
    messages,
    isLoading,
    error,
    sendMessage,
    initializeChat,
    reset,
    restoreMessages,
  } = useChat(redFlag, applicationData);
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasInitialized = useRef(false);
  const currentRedFlagRule = useRef(redFlag.rule);
  // Store separate conversation history for each red flag
  const conversationHistory = useRef<Map<string, ChatMessage[]>>(new Map());

  // Save/restore conversations when switching between red flags
  useEffect(() => {
    // Only act when switching between different non-empty rules
    if (
      redFlag.rule &&
      currentRedFlagRule.current &&
      redFlag.rule !== currentRedFlagRule.current
    ) {
      // Save current conversation before switching
      if (currentRedFlagRule.current && messages.length > 0) {
        conversationHistory.current.set(currentRedFlagRule.current, [
          ...messages,
        ]);
      }

      // Restore saved conversation or start fresh
      const savedConversation = conversationHistory.current.get(redFlag.rule);
      if (savedConversation && savedConversation.length > 0) {
        restoreMessages(savedConversation);
        hasInitialized.current = true;
      } else {
        reset();
        hasInitialized.current = false;
      }
    }
    // Update current rule tracker only for non-empty rules
    if (redFlag.rule) {
      currentRedFlagRule.current = redFlag.rule;
    }
  }, [redFlag.rule, messages, reset, restoreMessages]);

  // Initialize chat only once when modal first opens
  useEffect(() => {
    if (isOpen && !hasInitialized.current) {
      initializeChat();
      hasInitialized.current = true;
    }
    // Keep conversation history when closing - don't reset
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    await sendMessage(inputValue);
    setInputValue("");
  };

  const handleClose = () => {
    if (inputValue.trim()) {
      const confirmed = confirm(
        "You have unsent text. Are you sure you want to close?"
      );
      if (!confirmed) return;
    }
    onClose();
  };

  // Prevent closing when clicking outside - only X button can close
  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    // Do nothing - modal stays open
    e.stopPropagation();
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-black">
            Resolve Validation Issue
          </h2>
          <button
            onClick={handleClose}
            className="ml-4 text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Close"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2 ${
                  message.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-black"
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-lg px-4 py-2">
                <div className="flex gap-1">
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0ms" }}
                  />
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "150ms" }}
                  />
                  <div
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "300ms" }}
                  />
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
              <p className="text-sm text-red-800">
                <span className="font-semibold">Error:</span> {error}
              </p>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex gap-2">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder="Type your message..."
              disabled={isLoading}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <button
              type="button"
              onClick={handleSendMessage}
              disabled={isLoading || !inputValue.trim()}
              className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? (
                <svg
                  className="animate-spin h-5 w-5"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
              ) : (
                "Send"
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
