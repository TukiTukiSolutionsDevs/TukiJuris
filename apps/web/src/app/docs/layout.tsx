"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import {
  Zap,
  ExternalLink,
  ChevronRight,
  ChevronDown,
  Terminal,
  Code2,
} from "lucide-react";
import { PublicLayout } from "@/components/public/PublicLayout";
import { NAV_ITEMS } from "./_data/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function DocsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [tocOpen, setTocOpen] = useState(false);

  const activeSection = NAV_ITEMS.find((item) => pathname.startsWith(item.href))?.id ?? "getting-started";

  return (
    <PublicLayout hideFooter>
      <div className="flex min-h-full flex-col text-on-surface">
        {/* Top bar — sits below PublicHeader */}
        <div
          className="sticky top-16 sm:top-20 z-40 bg-background/95 backdrop-blur-sm"
          style={{ borderBottom: "1px solid rgba(79,70,51,0.15)" }}
        >
          <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Code2 className="w-4 h-4 text-primary" />
              <span className="font-bold text-sm text-on-surface">API Docs</span>
              <span
                className="ml-2 inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[10px] bg-primary/10 text-primary font-medium"
                style={{ border: "1px solid rgba(255,209,101,0.2)" }}
              >
                <Zap className="w-2.5 h-2.5" />
                v0.4
              </span>
            </div>
            <div className="flex items-center gap-2">
              <a
                href={`${API_URL}/docs`}
                target="_blank"
                rel="noopener noreferrer"
                className="hidden sm:flex items-center gap-1.5 text-xs text-on-surface/50 hover:text-primary transition-colors rounded-lg px-3 py-1.5"
                style={{ border: "1px solid rgba(79,70,51,0.15)" }}
              >
                <Terminal className="w-3.5 h-3.5" />
                Swagger UI
                <ExternalLink className="w-3 h-3" />
              </a>
              <a
                href={`${API_URL}/redoc`}
                target="_blank"
                rel="noopener noreferrer"
                className="hidden sm:flex items-center gap-1.5 text-xs text-on-surface/50 hover:text-primary transition-colors rounded-lg px-3 py-1.5"
                style={{ border: "1px solid rgba(79,70,51,0.15)" }}
              >
                <Code2 className="w-3.5 h-3.5" />
                ReDoc
                <ExternalLink className="w-3 h-3" />
              </a>
              {/* Mobile TOC toggle */}
              <button
                className="lg:hidden flex items-center gap-1.5 text-xs text-on-surface/50 hover:text-on-surface rounded-lg px-3 py-1.5 transition-colors"
                style={{ border: "1px solid rgba(79,70,51,0.15)" }}
                onClick={() => setTocOpen(!tocOpen)}
              >
                Contenidos
                <ChevronDown className={`w-3.5 h-3.5 transition-transform ${tocOpen ? "rotate-180" : ""}`} />
              </button>
            </div>
          </div>
          {/* Mobile TOC dropdown */}
          {tocOpen && (
            <div
              className="lg:hidden bg-background/98 px-4 py-3"
              style={{ borderTop: "1px solid rgba(79,70,51,0.15)" }}
            >
              <nav className="flex flex-wrap gap-1">
                {NAV_ITEMS.map((item) => (
                  <Link
                    key={item.id}
                    href={item.href}
                    onClick={() => setTocOpen(false)}
                    className={`px-3 py-1.5 rounded-lg text-xs transition-colors ${
                      activeSection === item.id
                        ? "bg-primary/10 text-primary font-medium"
                        : "text-on-surface/50 hover:text-on-surface hover:bg-surface-container-low"
                    }`}
                  >
                    {item.label}
                  </Link>
                ))}
              </nav>
            </div>
          )}
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex gap-0 lg:gap-10 w-full">
          {/* Sidebar TOC — sticky on desktop */}
          <aside className="hidden lg:block w-56 shrink-0">
            <div className="sticky top-[7.5rem] sm:top-[8.5rem] pt-10 pb-20">
              <p className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40 mb-4 font-medium">
                Contents
              </p>
              <nav className="space-y-0.5">
                {NAV_ITEMS.map((item) => (
                  <Link
                    key={item.id}
                    href={item.href}
                    className={`w-full text-left flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                      activeSection === item.id
                        ? "bg-surface-container-low text-primary font-medium"
                        : "text-on-surface/40 hover:text-on-surface hover:bg-surface-container-low"
                    }`}
                  >
                    {activeSection === item.id && (
                      <ChevronRight className="w-3 h-3 text-primary shrink-0" />
                    )}
                    <span className={activeSection === item.id ? "" : "ml-5"}>{item.label}</span>
                  </Link>
                ))}
              </nav>

              <div
                className="mt-8 p-3 rounded-lg bg-primary/5"
                style={{ border: "1px solid rgba(255,209,101,0.15)" }}
              >
                <p className="text-xs text-primary font-medium mb-1">Interactive testing</p>
                <p className="text-xs text-on-surface/40 mb-3">
                  Try all endpoints directly in your browser.
                </p>
                <a
                  href={`${API_URL}/docs`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-xs text-primary hover:text-primary/80 transition-colors"
                >
                  Open Swagger UI
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          </aside>

          {/* Main content — each section page renders here */}
          <main className="flex-1 min-w-0 py-8 sm:py-10">
            {children}
          </main>
        </div>
      </div>
    </PublicLayout>
  );
}
