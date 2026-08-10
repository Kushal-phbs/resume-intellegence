import { apiClient } from "./client";
import { API_ROUTES } from "@/constants/routes";
import type { ConversationResponse, MessageResponse, ChatResponse } from "@/types/chat";

export const chatApi = {
  listConversations: (limit = 50, offset = 0) =>
    apiClient
      .get<ConversationResponse[]>(API_ROUTES.conversations, { params: { limit, offset } })
      .then((r) => r.data),

  createConversation: (title?: string) =>
    apiClient
      .post<ConversationResponse>(API_ROUTES.conversations, { title })
      .then((r) => r.data),

  getConversation: (id: string) =>
    apiClient.get<ConversationResponse>(API_ROUTES.conversationById(id)).then((r) => r.data),

  renameConversation: (id: string, title: string) =>
    apiClient.patch<ConversationResponse>(API_ROUTES.conversationById(id), { title }).then((r) => r.data),

  deleteConversation: (id: string) =>
    apiClient.delete<void>(API_ROUTES.conversationById(id)).then((r) => r.data),

  listMessages: (conversationId: string, limit = 50, offset = 0) =>
    apiClient
      .get<MessageResponse[]>(API_ROUTES.messages(conversationId), { params: { limit, offset } })
      .then((r) => r.data),

  sendMessage: (conversationId: string, content: string) =>
    apiClient
      .post<ChatResponse>(API_ROUTES.messages(conversationId), { content })
      .then((r) => r.data),
};
