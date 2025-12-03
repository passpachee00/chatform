"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import type {
  ChatMessage,
  ChatSessionContext,
  ChatMessageResponse,
  RedFlag,
  ApplicationData,
} from "@/types";

interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (userMessage: string) => Promise<void>;
  initializeChat: () => Promise<void>;
  reset: () => void;
}

export function useChat(
  redFlag: RedFlag,
  applicationData: ApplicationData
): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  // Use refs to keep track of current values for use in callbacks
  const messagesRef = useRef<ChatMessage[]>([]);
  const isInitializedRef = useRef(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Sync refs with state
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  useEffect(() => {
    isInitializedRef.current = isInitialized;
  }, [isInitialized]);

  // Initialize chat with first message from assistant
  const initializeChat = useCallback(async () => {
    if (isInitializedRef.current) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/chat/message`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: "", // Empty message signals initialization
          redFlag,
          applicationData,
          conversationHistory: [],
        }),
        signal: AbortSignal.timeout(30000), // 30 second timeout
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data: ChatMessageResponse = await response.json();

      if (data.status === "error") {
        throw new Error(data.error || "Failed to initialize chat");
      }

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: data.content,
        timestamp: new Date(data.timestamp),
      };

      setMessages([assistantMessage]);
      setIsInitialized(true);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to initialize chat";
      setError(errorMessage);
      console.error("Chat initialization error:", err);
    } finally {
      setIsLoading(false);
    }
  }, [API_URL]);

  // Send user message and get assistant response
  const sendMessage = useCallback(
    async (userMessage: string) => {
      if (!userMessage.trim() || isLoading) return;

      setIsLoading(true);
      setError(null);

      // Add user message immediately
      const newUserMessage: ChatMessage = {
        role: "user",
        content: userMessage,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, newUserMessage]);

      // Use ref to get current messages (includes the one we just added via setState)
      // We need to manually include newUserMessage since setState is async
      const currentMessages = messagesRef.current;

      try {
        const response = await fetch(`${API_URL}/api/chat/message`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: userMessage,
            redFlag,
            applicationData,
            conversationHistory: [...currentMessages, newUserMessage],
          }),
          signal: AbortSignal.timeout(30000), // 30 second timeout
        });

        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }

        const data: ChatMessageResponse = await response.json();

        if (data.status === "error") {
          throw new Error(data.error || "Failed to send message");
        }

        const assistantMessage: ChatMessage = {
          role: "assistant",
          content: data.content,
          timestamp: new Date(data.timestamp),
        };

        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to send message";
        setError(errorMessage);
        console.error("Chat send message error:", err);

        // Remove the user message if request failed
        setMessages((prev) => prev.slice(0, -1));
      } finally {
        setIsLoading(false);
      }
    },
    [API_URL]
  );

  // Reset chat state
  const reset = useCallback(() => {
    setMessages([]);
    setIsLoading(false);
    setError(null);
    setIsInitialized(false);
    messagesRef.current = [];
    isInitializedRef.current = false;
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    initializeChat,
    reset,
  };
}
