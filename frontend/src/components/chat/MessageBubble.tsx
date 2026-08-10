import { useState } from "react";
import { Copy, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { MessageResponse } from "@/types/chat";

/* Minimal markdown: bold, inline code, fenced code blocks */
function renderContent(text: string) {
  const fenceRegex = /```(\w*)\n?([\s\S]*?)```/g;
  const parts: React.ReactNode[] = [];
  let last = 0;
  let match: RegExpExecArray | null;

  while ((match = fenceRegex.exec(text)) !== null) {
    if (match.index > last) parts.push(renderInline(text.slice(last, match.index), match.index));
    parts.push(
      <pre key={match.index} className="my-2 overflow-x-auto rounded-md bg-muted p-3 text-xs font-mono">
        <code>{match[2]}</code>
      </pre>
    );
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push(renderInline(text.slice(last), last));
  return parts;
}

function renderInline(text: string, key: number | string) {
  const chunks = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return (
    <span key={key}>
      {chunks.map((c, i) => {
        if (c.startsWith("**") && c.endsWith("**"))
          return <strong key={i}>{c.slice(2, -2)}</strong>;
        if (c.startsWith("`") && c.endsWith("`"))
          return <code key={i} className="rounded bg-muted px-1 py-0.5 text-xs font-mono">{c.slice(1, -1)}</code>;
        return <span key={i}>{c}</span>;
      })}
    </span>
  );
}

export function MessageBubble({ message }: { message: MessageResponse }) {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard?.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className={cn("group flex gap-2", isUser ? "flex-row-reverse" : "flex-row")}>
      <div
        className={cn(
          "relative max-w-[78%] rounded-lg px-3.5 py-2.5 text-sm leading-relaxed",
          isUser
            ? "bg-primary/10 text-foreground"
            : "bg-muted text-foreground"
        )}
      >
        <div className="whitespace-pre-wrap break-words">{renderContent(message.content)}</div>
        <button
          onClick={copy}
          aria-label="Copy message"
          className="absolute -top-2 right-1 hidden rounded-md bg-card border border-border p-1 text-muted-foreground hover:text-foreground group-hover:flex"
        >
          {copied ? <Check className="h-3 w-3 text-success" /> : <Copy className="h-3 w-3" />}
        </button>
      </div>
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="flex gap-2">
      <div className="flex items-center gap-1 rounded-lg bg-muted px-3.5 py-2.5">
        {[0, 150, 300].map((delay) => (
          <span
            key={delay}
            className="h-1.5 w-1.5 rounded-full bg-muted-foreground/60"
            style={{ animation: `bounce 1s ${delay}ms infinite` }}
          />
        ))}
      </div>
      <style>{`
        @keyframes bounce {
          0%, 100% { transform: translateY(0); opacity: .4; }
          50%       { transform: translateY(-4px); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
