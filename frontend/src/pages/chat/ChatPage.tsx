import { useState } from "react";
import { MessageSquare } from "lucide-react";
import { useConversations, useCreateConversation } from "@/hooks/useChat";
import { ConversationList } from "@/components/chat/ConversationList";
import { MessageThread } from "@/components/chat/MessageThread";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/common/ErrorState";
import { EmptyState } from "@/components/common/EmptyState";
import { cn } from "@/lib/utils";

export function ChatPage() {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const { data: conversations, isLoading, isError, error, refetch } = useConversations();
  const createConversation = useCreateConversation();

  const handleNew = () => {
    createConversation.mutate(undefined, {
      onSuccess: (c) => setActiveId(c.id),
    });
  };

  const activeConversation = conversations?.find((c) => c.id === activeId);

  return (
    // Full-height layout that fits inside the AppLayout's <main> scroll area
    <div className="flex h-[calc(100vh-var(--nav-h,64px)-3rem)] min-h-[400px] overflow-hidden rounded-lg border border-border bg-card">
      {/* Sidebar */}
      <div
        className={cn(
          "shrink-0 border-r border-border transition-all duration-200",
          sidebarOpen ? "w-64" : "w-0 overflow-hidden"
        )}
      >
        {isLoading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
          </div>
        ) : isError ? (
          <div className="p-4">
            <ErrorState error={error} onRetry={() => refetch()} />
          </div>
        ) : (
          <ConversationList
            conversations={conversations ?? []}
            activeId={activeId}
            onSelect={(id) => setActiveId(id)}
            onNew={handleNew}
            isCreating={createConversation.isPending}
          />
        )}
      </div>

      {/* Toggle sidebar button (hairline) */}
      <button
        onClick={() => setSidebarOpen((o) => !o)}
        className="w-1 shrink-0 bg-transparent hover:bg-muted-foreground/20 transition-colors"
        aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
      />

      {/* Thread panel */}
      <div className="flex min-w-0 flex-1 flex-col">
        {!activeId ? (
          <div className="flex flex-1 items-center justify-center p-6">
            <EmptyState
              icon={MessageSquare}
              title="Select a conversation"
              description="Choose a conversation from the sidebar, or start a new one."
              actionLabel="New Conversation"
              onAction={handleNew}
            />
          </div>
        ) : !activeConversation ? (
          <div className="flex flex-1 items-center justify-center">
            <Skeleton className="h-10 w-48" />
          </div>
        ) : (
          <MessageThread
            conversationId={activeConversation.id}
            conversationTitle={activeConversation.title}
          />
        )}
      </div>
    </div>
  );
}
