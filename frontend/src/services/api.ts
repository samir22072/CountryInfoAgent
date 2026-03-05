import { TaskUpdate } from "../types";

const API_BASE_URL = "http://127.0.0.1:8000";

export const apiService = {
    async startChat(messages: { role: string; content: string }[]): Promise<string> {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ messages }),
        });

        if (!response.ok) {
            throw new Error(`Failed to start chat: ${response.status}`);
        }

        const { task_id } = await response.json();
        return task_id;
    },

    async getTaskStatus(taskId: string): Promise<TaskUpdate> {
        const response = await fetch(`${API_BASE_URL}/chat/${taskId}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch task status: ${response.status}`);
        }

        return await response.json();
    },
};
