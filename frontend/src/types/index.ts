export type Thought = {
    nodeName: string;
    payload: any;
};

export type Message = {
    role: "user" | "bot";
    content: string;
    thoughts?: Thought[];
};

export type TaskStatus = "pending" | "running" | "completed" | "failed";

export type TaskUpdate = {
    task_id: string;
    status: TaskStatus;
    thoughts: string[];
    result?: string;
    error?: string;
};
