"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { AppSidebar } from "./AppSidebar";
import { getToken } from "@/lib/auth";

interface AppLayoutProps {
  children: React.ReactNode;
  sidebarContent?: React.ReactNode;
}

export function AppLayout({ children, sidebarContent }: AppLayoutProps) {
  const pathname = usePathname();

  // Client-side auth guard — redirect to landing if no token
  useEffect(() => {
    const token = getToken();
    if (!token) {
      window.location.href = "/landing";
    }
  }, []);

  return (
    <div className="flex h-screen bg-[#0a0a0f] overflow-hidden">
      <AppSidebar currentPath={pathname ?? "/"}>
        {sidebarContent}
      </AppSidebar>
      <main className="flex-1 overflow-hidden bg-[#12121a] flex flex-col">
        {children}
      </main>
    </div>
  );
}
