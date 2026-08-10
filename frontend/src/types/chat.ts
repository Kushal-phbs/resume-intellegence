// Mirrors backend/app/schemas/chat.py exactly.

export type MessageRole = "user" | "assistant" | "system";

export interface ConversationCreate {
  title?: string; // defaults server-side to "New Conversation"
}

export interface ConversationUpdate {
  title: string;
}

export interface ConversationResponse {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface MessageCreate {
  content: string; // 1-4000 chars
}

export interface MessageResponse {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  token_count: number;
  created_at: string;
}

export interface ChatResponse {
  conversation: ConversationResponse;
  user_message: MessageResponse;
  assistant_message: MessageResponse;
  token_usage: Record<string, number>;
  processing_time: number;
}
