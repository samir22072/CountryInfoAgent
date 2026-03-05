"use client";

import React from "react";

interface ChatInputProps {
    input: string;
    setInput: (value: string) => void;
    onSubmit: (e: React.FormEvent) => void;
    isLoading: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ input, setInput, onSubmit, isLoading }) => {
    return (
        <div className="input-container">
            <form onSubmit={onSubmit} className="input-form">
                <input
                    type="text"
                    className="chat-input"
                    placeholder="Ask about a country..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    disabled={isLoading}
                />
                <button
                    type="submit"
                    className="send-button"
                    disabled={!input.trim() || isLoading}
                >
                    Send
                </button>
            </form>
        </div>
    );
};
