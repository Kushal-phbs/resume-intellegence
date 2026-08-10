import { useEffect, useRef, useState } from "react";
import { Send, ArrowDown, MessageSquare } from "lucide-react";
import { useMessages, useSendMessage } from "@/hooks/useChat";
import { MessageBubble, TypingIndicator } from "./MessageBubble";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/common/ErrorState";
import { EmptyState } from "@/components/common/EmptyState";
import type { MessageResponse } from "@/types/chat";

interface Props {
  conversationId: string;
  conversationTitle: string;
}

export function MessageThread({ conversationId, conversationTitle }: Props) {
  const [input, setInput] = useState("");
  const [localMessages, setLocalMessages] = useState<MessageResponse[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const { data: serverMessages, isLoading, isError, error, refetch } = useMessages(conversationId);
  const sendMsg = useSendMessage(conversationId);

  // Sync server messages into local state (server is source of truth)
  useEffect(() => {
    if (serverMessages) setLocalMessages(serverMessages);
  }, [serverMessages]);

  // Auto-scroll on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [localMessages, isTyping]);

  const onScroll = () => {
    const el = listRef.current;
    if (!el) return;
    setShowScrollBtn(el.scrollHeight - el.scrollTop - el.clientHeight > 120);
  };

  const send = () => {
    const content = input.trim();
    if (!content || sendMsg.isPending) return;
    setInput("");

    // Optimistic: show user message + typing indicator immediately
    const tempUser: MessageResponse = {
      id: `temp-${Date.now()}`,
      conversation_id: conversationId,
      role: "user",
      content,
      token_count: 0,
      created_at: new Date().toISOString(),
    };
    setLocalMessages((prev) => [...prev, tempUser]);
    setIsTyping(true);

    sendMsg.mutate(content, {
      onSuccess: (resp) => {
        // Replace temp message + add assistant message from server
        setLocalMessages((prev) => [
          ...prev.filter((m) => m.id !== tempUser.id),
          resp.user_message,
          resp.assistant_message,
        ]);
        setIsTyping(false);
      },
      onError: () => {
        // Roll back optimistic message
        setLocalMessages((prev) => prev.filter((m) => m.id !== tempUser.id));
        setIsTyping(false);
      },
    });
  };

  if (isLoading) {
    return (
      <div className="flex flex-col gap-3 p-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className={`h-14 w-2/3 ${i % 2 === 1 ? "ml-auto" : ""}`} />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-6">
        <ErrorState error={error} onRetry={() => refetch()} />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b border-border px-4 py-3">
        <h2 className="truncate text-sm font-semibold">{conversationTitle}</h2>
      </div>

      {/* Messages */}
      <div
        ref={listRef}
        className="relative flex-1 overflow-y-auto p-4"
        onScroll={onScroll}
      >
        {localMessages.length === 0 && !isTyping ? (
          <EmptyState
            icon={MessageSquare}
            title="No messages yet"
            description="Send a message to start the conversation."
          />
        ) : (
          <div className="flex flex-col gap-3">
            {localMessages
              .filter((m) => m.role !== "system")
              .map((m) => (
                <MessageBubble key={m.id} message={m} />
              ))}
            {isTyping && <TypingIndicator />}
          </div>
        )}
        <div ref={bottomRef} />

        {showScrollBtn && (
          <button
            onClick={() => bottomRef.current?.scrollIntoView({ behavior: "smooth" })}
            className="absolute bottom-4 left-1/2 flex h-8 w-8 -translate-x-1/2 items-center justify-center rounded-full border border-border bg-card shadow-md hover:bg-muted"
            aria-label="Scroll to bottom"
          >
            <ArrowDown className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-border p-3">
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
            }}
            placeholder="Message the AI… (Shift+Enter for new line)"
            rows={1}
            className="flex-1 resize-none rounded-md border border-border bg-background px-3 py-2 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-primary"
            style={{ maxHeight: 140, overflowY: "auto" }}
          />
          <Button
            onClick={send}
            disabled={!input.trim() || sendMsg.isPending}
            isLoading={sendMsg.isPending}
            size="icon"
            aria-label="Send message"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        {sendMsg.isError && (
          <p className="mt-1.5 text-xs text-destructive">Failed to send. Please try again.</p>
        )}
      </div>
    </div>
  );
}
