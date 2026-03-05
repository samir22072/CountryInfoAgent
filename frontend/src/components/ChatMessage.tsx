"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import { Message } from "../types";
import { ThoughtProcess } from "./ThoughtProcess";

interface ChatMessageProps {
    message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
    return (
        <div className={`message message-${message.role}`}>
            <div className="message-content">
                {message.role === "bot" && <strong>Agent</strong>}
                {message.role === "user" && <strong>You</strong>}

                {message.thoughts && <ThoughtProcess thoughts={message.thoughts} />}

                {message.content && (
                    <div className="message-text">
                        {message.role === "bot" ? (
                            <ReactMarkdown>{message.content}</ReactMarkdown>
                        ) : (
                            <p>{message.content}</p>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};
