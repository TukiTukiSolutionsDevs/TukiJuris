import { Key } from "lucide-react";

export function ScopeBadge({ scope }: { scope: string }) {
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-xs bg-primary/10 text-primary"
      style={{ border: "1px solid rgba(255,209,101,0.2)" }}
    >
      <Key className="w-2.5 h-2.5" />
      {scope}
    </span>
  );
}
