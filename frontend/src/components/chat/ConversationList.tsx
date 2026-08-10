import { useState } from "react";
import { Pencil, Trash2, Check, X, Plus, MessageSquare } from "lucide-react";
import { cn, formatRelative } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/common/EmptyState";
import { useRenameConversation, useDeleteConversation } from "@/hooks/useChat";
import type { ConversationResponse } from "@/types/chat";

interface Props {
  conversations: ConversationResponse[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  isCreating: boolean;
}

export function ConversationList({ conversations, activeId, onSelect, onNew, isCreating }: Props) {
  const rename = useRenameConversation();
  const del = useDeleteConversation();
  const [editId, setEditId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  const startEdit = (c: ConversationResponse) => {
    setEditId(c.id);
    setEditTitle(c.title);
  };

  const confirmRename = (id: string) => {
    if (editTitle.trim()) rename.mutate({ id, title: editTitle.trim() });
    setEditId(null);
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-border p-4">
        <h2 className="text-sm font-semibold">Conversations</h2>
        <Button size="sm" onClick={onNew} isLoading={isCreating} aria-label="New conversation">
          <Plus className="h-3.5 w-3.5" />
          New
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {conversations.length === 0 ? (
          <div className="py-8">
            <EmptyState
              icon={MessageSquare}
              title="No conversations"
              description="Start a new conversation to chat with the AI."
              actionLabel="New Conversation"
              onAction={onNew}
            />
          </div>
        ) : (
          conversations.map((c) => (
            <div
              key={c.id}
              className={cn(
                "group flex cursor-pointer items-start gap-2 rounded-md p-2.5 transition-colors",
                activeId === c.id ? "bg-primary/10" : "hover:bg-muted"
              )}
              onClick={() => onSelect(c.id)}
            >
              <div className="min-w-0 flex-1">
                {editId === c.id ? (
                  <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                    <Input
                      autoFocus
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") confirmRename(c.id);
                        if (e.key === "Escape") setEditId(null);
                      }}
                      className="h-7 text-xs"
                    />
                    <button onClick={() => confirmRename(c.id)} className="text-success hover:opacity-70" aria-label="Confirm rename">
                      <Check className="h-3.5 w-3.5" />
                    </button>
                    <button onClick={() => setEditId(null)} className="text-muted-foreground hover:opacity-70" aria-label="Cancel rename">
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ) : (
                  <>
                    <p className={cn("truncate text-sm font-medium", activeId === c.id ? "text-primary" : "text-foreground")}>
                      {c.title}
                    </p>
                    <p className="mt-0.5 text-xs text-muted-foreground">{formatRelative(c.updated_at)}</p>
                  </>
                )}
              </div>

              {editId !== c.id && (
                <div className="flex shrink-0 gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
                  <button
                    onClick={(e) => { e.stopPropagation(); startEdit(c); }}
                    className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                    aria-label="Rename conversation"
                  >
                    <Pencil className="h-3 w-3" />
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); del.mutate(c.id); }}
                    className="rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                    aria-label="Delete conversation"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
