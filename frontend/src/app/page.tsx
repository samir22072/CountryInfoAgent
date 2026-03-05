"use client";

import { useState, useRef, useEffect } from "react";
import Head from "next/head";
import { Message } from "../types";
import { apiService } from "../services/api";
import { Header } from "../components/Header";
import { ChatMessage } from "../components/ChatMessage";
import { ChatInput } from "../components/ChatInput";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "bot", content: "Hi there! Ask me anything about any country! For example: 'What is the population of Germany?' or 'What currency does Japan use?'" }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // 1. Start the task
      const taskId = await apiService.startChat(
        [...messages, userMessage].map((m) => ({ role: m.role, content: m.content }))
      );

      // Add a placeholder bot message
      setMessages((prev) => [
        ...prev,
        { role: "bot", content: "", thoughts: [] },
      ]);

      // 2. Poll for updates
      let taskCompleted = false;
      const pollInterval = 1000; // 1 second

      while (!taskCompleted) {
        await new Promise((resolve) => setTimeout(resolve, pollInterval));

        const taskUpdate = await apiService.getTaskStatus(taskId);

        // Update thoughts and content
        setMessages((prev) => {
          const newMsgs = [...prev];
          const lastBotMsg = newMsgs[newMsgs.length - 1];

          if (taskUpdate.thoughts) {
            // Map thoughts to the internal format
            lastBotMsg.thoughts = taskUpdate.thoughts.map((t: string) => ({
              nodeName: "step",
              payload: t
            }));
          }

          if (taskUpdate.result) {
            lastBotMsg.content = taskUpdate.result;
          }

          if (taskUpdate.error) {
            lastBotMsg.content = `Error: ${taskUpdate.error}`;
          }

          return newMsgs;
        });

        if (taskUpdate.status === "completed" || taskUpdate.status === "failed") {
          taskCompleted = true;
        }
      }
    } catch (error) {
      console.error("Failed to process transaction:", error);
      setMessages((prev) => {
        const newMsgs = [...prev];
        if (newMsgs[newMsgs.length - 1].role === "bot" && newMsgs[newMsgs.length - 1].content === "") {
          newMsgs.pop();
        }
        return [
          ...newMsgs,
          { role: "bot", content: "Sorry, I encountered an error. Is the backend running?" },
        ];
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Country Information AI</title>
      </Head>
      <main>
        <Header />

        <div className="chat-container">
          <div className="chat-messages">
            {messages.map((msg, idx) => (
              <ChatMessage key={idx} message={msg} />
            ))}
            {isLoading && (
              <div className="message message-bot">
                <div className="message-content loading-dots">
                  <div className="dot"></div>
                  <div className="dot"></div>
                  <div className="dot"></div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <ChatInput
            input={input}
            setInput={setInput}
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />
        </div>
      </main>
    </>
  );
}
