"use client";

import { useState } from "react";
import { Terminal, Copy, Check } from "lucide-react";

interface CodeBlockProps {
  lang: string;
  code: string;
}

export function CodeBlock({ lang, code }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className="relative rounded-lg bg-surface-container-lowest overflow-hidden"
      style={{ border: "1px solid rgba(79,70,51,0.15)" }}
    >
      <div
        className="flex items-center justify-between px-4 py-2 bg-surface-container-lowest"
        style={{ borderBottom: "1px solid rgba(79,70,51,0.15)" }}
      >
        <div className="flex items-center gap-2">
          <Terminal className="w-3.5 h-3.5 text-on-surface/30" />
          <span className="text-xs text-on-surface/30 font-mono">{lang}</span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-xs text-on-surface/40 hover:text-on-surface transition-colors"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-[#10B981]" />
              <span className="text-[#10B981]">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className="p-4 text-sm font-mono leading-relaxed overflow-x-auto text-on-surface whitespace-pre">
        <code>{code}</code>
      </pre>
    </div>
  );
}
