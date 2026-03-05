"use client";

import React, { useState } from "react";
import { Thought } from "../types";

interface ThoughtProcessProps {
    thoughts: Thought[];
}

export const ThoughtProcess: React.FC<ThoughtProcessProps> = ({ thoughts }) => {
    const [isExpanded, setIsExpanded] = useState(false);

    if (!thoughts || thoughts.length === 0) return null;

    return (
        <div className="thoughts-container">
            <div
                className={`thoughts-header ${isExpanded ? 'expanded' : ''}`}
                onClick={() => setIsExpanded(!isExpanded)}
                style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
            >
                <span>Thought Process</span>
                <span className="toggle-icon">{isExpanded ? "−" : "+"}</span>
            </div>
            {isExpanded && (
                <div className="thoughts-list">
                    {thoughts.map((thought, tIdx) => (
                        <div key={tIdx} className="thought-item">
                            <div className="thought-node">✓ {thought.nodeName}</div>
                            {thought.payload && (
                                <div className="thought-payload">
                                    {String(thought.payload)}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};
