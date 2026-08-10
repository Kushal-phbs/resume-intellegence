import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { chatApi } from "@/api/chat";
import { queryKeys } from "@/constants/queryKeys";

export function useConversations() {
  return useQuery({ queryKey: queryKeys.conversations, queryFn: () => chatApi.listConversations() });
}

export function useMessages(conversationId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.messages(conversationId ?? ""),
    queryFn: () => chatApi.listMessages(conversationId as string),
    enabled: !!conversationId,
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (title?: string) => chatApi.createConversation(title),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.conversations }),
  });
}

export function useRenameConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) => chatApi.renameConversation(id, title),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.conversations }),
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => chatApi.deleteConversation(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.conversations }),
  });
}

export function useSendMessage(conversationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (content: string) => chatApi.sendMessage(conversationId, content),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.messages(conversationId) }),
  });
}
