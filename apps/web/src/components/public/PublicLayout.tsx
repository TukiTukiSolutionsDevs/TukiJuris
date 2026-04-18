"use client";

import { PublicHeader } from "./PublicHeader";
import { PublicFooter } from "./PublicFooter";

interface PublicLayoutProps {
  children: React.ReactNode;
  /** Hide footer on specific pages like auth */
  hideFooter?: boolean;
}

export function PublicLayout({ children, hideFooter = false }: PublicLayoutProps) {
  return (
    <div className="min-h-screen bg-background text-on-surface font-body flex flex-col">
      <PublicHeader />
      <main className="flex-1 pt-16 sm:pt-20">
        {children}
      </main>
      {!hideFooter && <PublicFooter />}
    </div>
  );
}
